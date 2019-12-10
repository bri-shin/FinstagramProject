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


class likeTable(Table):
    id = Col('Id', show=False)
    username = Col("Username")
    rating = Col("Rating (out of 10)")


class Tag_Table(Table):
    username = Col("Username")
    fname = Col("First Name")
    lname = Col("Last Name")


class Analytics_Reactions(Table):
    photoID = Col('Photo ID')
    photoPoster = Col('Posted By')
    display_likes = Col('Number of Reactions')


class Analytics_Rating(Table):
    photoID = Col('Photo ID')
    photoPoster = Col('Posted By')
    tot_rating = Col('Total Rating')


class commentTable(Table):
    id = Col('Id', show=False)
    username = Col("Username")
    comment = Col("Comments")


class followerTable(Table):
    username_followed = Col("Username")
