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

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.load(
    open('client_secrets.json', 'r').read())['web']['client_id']

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
    return render_template('login.html')


if __name__ == "__main__":
    app.secret_key = 'super_secret_key'
    app.debug = True #built-in auto reloader when code is changed (only when marked True)
    app.run(host = '0.0.0.0', port = 5000)

@app.route('/gconnect', methods=["POST"])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid stateparameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data
    try:
        #upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope = '')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)

    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
        #check that the access token is valid.
        access_token = credentials.access_token
        url = (('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s') % access_token)
        h = httplib2.Http()
        result = json.loads(h.request(url,'GET')[1])

        if result.get('error') is not None:
            response = make_response(json.dumps(result.get('error')),500)
            response.headers['Content-Type'] = 'application/json'
            #Verify that the access token is used for the intended user.
            gplus_id = credentials.id_token['sub']
            if result['user_id'] != gplus_id:
                response = make_response(json.dumps("Token's user ID doesn't match given the user ID"), 401)
                response.headers['Content-Type'] = 'application/json'
                return response
            #check to see if user is already logged in
            stored_credentials = login_session.get('credentials')
            stored_gplus_id = login_session.get('gplus_id')
            if stored_credentials is not None and gplus_id == stored_gplus_id:
                response = make_response(json.dumps('Current user is already connected'), 200)
                response.headers['Content-Type']  = 'application/json'

            #get user info
            userinfo_url = "https:/www.googleapis.com/oauth2/v1/userinfo"
            params ={'access_token' : credentials.access_token, 'alt' :'json'}
            answer  = requests.get(userinfo_url, params=params)
            data = json.loads(answer.text)

            login_session['username'] = data["name"]
            login_session['picture'] = data["picture"]
            login_session['email'] = data['email']

            output = "login successful " + login_session['username'] + "!"
            flash("you are not logged in %s" %login_session['username'])
            return output
