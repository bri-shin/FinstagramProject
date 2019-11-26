from flask_table import Table, Col, LinkCol

class Results(Table):
    id = Col('Id', show=False)
    photoID = Col('Photo ID')
    photoPoster = Col('Posted By')