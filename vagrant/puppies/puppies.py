from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Shelter, Puppy

import datetime

engine = create_engine('sqlite:///puppies.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()

q = session.query(Puppy).order_by(Puppy.name.asc()).all()
for puppy in q:
    print puppy.name

sixMonthsAgo = datetime.date.today() - datetime.timedelta(weeks=24)
q = session.query(Puppy).filter(Puppy.dateOfBirth > sixMonthsAgo)\
                        .order_by(Puppy.dateOfBirth.desc()).all()
for puppy in q:
    print puppy.id, puppy.name, puppy.dateOfBirth.isoformat()

q = session.query(Puppy).order_by(Puppy.weight.asc()).all()
for puppy in q:
    print puppy.id, puppy.name, puppy.weight

q = session.query(Shelter, func.count(Puppy.id)).join(Puppy).group_by(Shelter.id).all()
for item in q:
    print item[0].id, item[0].name, item[1]
