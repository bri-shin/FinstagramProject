from flask_table import Table, Col, LinkCol


class Results(Table):
    id = Col('Id', show=False)
    photoID = Col('Photo ID')
    photoPoster = Col('Posted By')


class followTable(Table):
    id = Col('Id', show=False)
    username_follower = Col("Username")
    accept = LinkCol('Accept', 'followAccept',
                     url_kwargs=dict(username='username_follower'))
    decline = LinkCol('Decline', 'followDecline',
                      url_kwargs=dict(username='username_follower'))
