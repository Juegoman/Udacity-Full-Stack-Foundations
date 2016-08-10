import sys

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    """User table definition"""
    __tablename__ = 'user'

    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250), nullable=False)
    id = Column(Integer, primary_key=True)


class Restaurant(Base):
    """Restaurant table definition"""
    __tablename__ = 'restaurant'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Returns object data in easily serializable format"""
        return {
            'name': self.name,
            'id': self.id,
        }


class MenuItem(Base):
    """MenuItem table definition"""
    __tablename__ = 'menu_item'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)

    course = Column(String(250))
    description = Column(String(250))
    price = Column(String(8))

    restaurant_id = Column(Integer, ForeignKey('restaurant.id'))
    restaurant = relationship(Restaurant)

    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Returns object data in easily serializable format"""
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'price': self.price,
            'course': self.course,
        }

engine = create_engine('sqlite:///restaurantmenu.db')

Base.metadata.create_all(engine)
