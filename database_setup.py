# -*- coding: utf-8 -*-
"""
This is setting up database in Flask
"""
#This is configuration code for SQLalchemy
import sys

from sqlalchemy import Column, ForeignKey, Integer, String

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship

from sqlalchemy import create_engine

Base = declarative_base()

#defining classes of the database

class Restaurant(Base):
    
    #this is our table element
    __tablename__ = 'restaurant'
    
    #mapper code creates variables that are used to create columns
    name= Column(String(80),
                 nullable = False)
                 
    id = Column(Integer,
                primary_key = True)

class MenuItems(Base):
    
    #this is our table element
    __tablename__ = 'menu_item'
    
    #mapper code creates variables that are used to create columns
    
    name = Column(String(80),
                  nullable = False)
    
    id = Column(Integer,
                primary_key = True)
    
    course = Column(String(250))

    description = Column(String(250))

    price = Column(String(8))
    
    restaurant_id = Column(Integer,
                           ForeignKey('restaurant.id'))                
     
    restaurant = relationship(Restaurant)
    
    #this becomes a property of MenuItem objects
    @property
    def serialize(self):
        #returns object data in easily serializeable format
        return {
            'name' : self.name,
            'description': self.description,
            'course' : self.course,
            'id' : self.id,
            'price' : self.price,        
        }
    
    #mapper code creates variables that are used to create columns

#insert at end of code (end of configuration)

engine= create_engine('sqlite:///restaurantmenu.db')

Base.metadata.create_all(engine) #this line goes in and creates all the 
#objects for the database