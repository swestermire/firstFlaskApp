# -*- coding: utf-8 -*-
"""
Created on Sun Oct 23 18:59:13 2016

@author: HappyForYou

Introduction to App development in Flask
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from flask import jsonify
from flask_bootstrap import Bootstrap

app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItems


from flask import session as login_session
import random, string

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

#Making an API endpoint (GET Request)
@app.route('/restaurants/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    items = session.query(MenuItems).filter_by(restaurant_id = restaurant.id).all()
    return jsonify(MenuItems=[i.serialize for i in items])

#Making an another API endpoint
@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    item = session.query(MenuItems).filter_by(id = menu_id).one()
    return jsonify(MenuItems=item.serialize)

@app.route('/') #decorator that wraps our function in the app.route() function
#essentially, this establishes our /hello route which then executes HelloWorld()
@app.route('/restaurants/')
@app.route('/restaurant/')
def restaurantsPage():
    restaurants = session.query(Restaurant).all()
    items = session.query(MenuItems).all()
    return render_template('restaurants.html',
                            restaurants = restaurants,
                            items = items)

    
#individual restaurant pages
@app.route('/restaurants/<int:restaurant_id>/') #notice our restaurant_id is passed
@app.route('/restaurant/<int:restaurant_id>/')
#restaurant_id is now an available value for us to retreive data from server
def restaurantMenu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItems).filter_by(restaurant_id = restaurant_id).all()
    
    return render_template('menu.html',
                           restaurant = restaurant,
                           items = items)

#default @app.route has GET requests. To have POST requests
#use
@app.route('/restaurant/<int:restaurant_id>/newMenuItem/', 
           methods=['GET','POST'])             
@app.route('/restaurants/<int:restaurant_id>/newMenuItem/', 
           methods=['GET','POST'])
def newMenuItem(restaurant_id):
    
    #this looks for POST requests
    if request.method == 'POST':
        newItem = MenuItems(name=request.form['name'],restaurant_id=restaurant_id)
        session.add(newItem)
        session.commit()
        flash("new menu item created!")
        return redirect(url_for('restaurantMenu',restaurant_id=restaurant_id))
    
    else:
        return render_template('newmenuitem.html', 
                               restaurant_id=restaurant_id)
     
    #render templates is the default template and manages the
    #view for this page
    
    #{{ something }} returns text in HTML form
    #look up documentation for how to embed python code into HTML
    #return render_template('menu.html', restaurant=restaurant, items = items)
    
@app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/editMenuItem/',
           methods = ['GET','POST'])
           
def editMenuItem(restaurant_id, menu_id):
    
    if request.method == 'POST':
        item = session.query(MenuItems).filter_by(id=menu_id).one()
        original_name = item.name        
        item.name = request.form['name']
        session.add(item)
        session.commit()
        message = original_name + " was editted to " + item.name
        flash(message)
        return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
    
    else:
        restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
        menu_item = session.query(MenuItems).filter_by(id=menu_id).one()
        return render_template('editmenuitem.html',
                               restaurant = restaurant,
                               menu_item=menu_item)

@app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/deleteMenuItem/',
           methods = ['GET','POST'])
           
def deleteMenuItem(restaurant_id, menu_id):
    
    if request.method == 'POST':

        result = request.form.get("True")
                
        
        if result:
            menuItem = session.query(MenuItems).filter_by(id=menu_id).one()
            restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()            
            session.delete(menuItem)
            session.commit()
            return redirect(url_for('restaurantMenu',
                                    restaurant_id=restaurant_id))
        elif not result:
            return redirect(url_for('restaurantMenu',
                                    restaurant_id=restaurant_id))
        else:
            return redirect(url_for('restaurantMenu',
                                    restaurant_id=restaurant_id))
                                    
    else:
        
        restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
        menuItem = session.query(MenuItems).filter_by(id=menu_id).one()
        return render_template('deletemenuitem.html',
                               restaurant = restaurant,
                               menuItem = menuItem)

#attempting authentication
@app.route('/login')
def showLogin():
    #anti-forgery token
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    return "The current session state is %s" %login_session['state']


if __name__ == "__main__":
    app.secret_key = 'super_secret_key'
    app.debug = True #built-in auto reloader when code is changed (only when marked True)
    app.run(host = '0.0.0.0', port = 5000)
