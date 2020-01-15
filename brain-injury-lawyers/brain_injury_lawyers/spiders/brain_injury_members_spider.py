import scrapy


class BrainInjuryMemberSpider(scrapy.Spider):
    name = "brain-injury"
    handle_httpstatus_list = [404]
    start_urls = [
        'https://nbitla.org/brain-injury-trial-lawyers/members/',
    ]

    def parse(self, response):
        members_list = response.css('ul#members-list').css('div.item-title').css('a')
        for a in members_list:
            href = a.css('a::attr(href)').get()
            name = a.css('a::text').get()
            yield response.follow(href, self.parse_member,
                                  cb_kwargs={
                                      'r': {'FirstName': name.split()[0], 'Last Name': name.split()[1], 'URL': href}},
                                  dont_filter=True)

        # follow pagination links
        for href in response.css('a.next.page-numbers::attr(href)'):
            yield response.follow(href, self.parse)

    def parse_member(self, response, r):
        if response.status == 404:
            yield r
        else:
            fields = response.css('table.profile-fields tr td.label::text').getall()[:-1]  # skip bio
            values = []
            for _ in response.css('table.profile-fields tr td p')[:len(fields)]:
                t = _.css('p::text').get()
                if not t:
                    t = _.css('p a::attr(href)').get()
                values.append(t)

            fieldmap = {'Firm': 'Law Firm',
                        'Phone': 'Phone #',
                        'Firm Website': 'Website (if provided)',
                        'Zip': 'Zip Code',
                        'Address': 'Address',
                        'City': 'City',
                        'State': 'State',
                        'Email': 'Email'}

            if not fields:
                yield r
            else:
                for field, value in zip(fields, values):
                    if field == 'Name':
                        continue
                    if field == 'Address 2':
                        r.update({'Address': r['Address'] + ' ' + value})
                    else:
                        r.update({fieldmap[field]: value})

                for _ in list(fieldmap) + ['FirstName', 'Last Name']:
                    if _ in ('Firm', 'Zip', 'Firm Website', 'Phone'):
                        continue
                    if _ not in r:
                        r.update({_: None})

                yield r
