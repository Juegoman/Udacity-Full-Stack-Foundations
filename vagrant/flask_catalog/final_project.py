from flask import Flask, render_template, request, redirect, url_for, flash, \
                  jsonify

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem, User

from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

# initialize flask
app = Flask(__name__)

# get client id for google oauth
G_CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

# initialize the database connection
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
@app.route('/restaurants')
def showRestaurants():
    """
    root route.
    Displays(READ) item categories, in this context restaurants.
    """
    # READ the list of restaurants
    restaurants = session.query(Restaurant).all()
    # check if user is logged in.
    if 'user_id' not in login_session:
        # if not logged in return a public list of restaurants
        return render_template('publicrestaurants.html',
                               restaurants=restaurants,
                               session=login_session)
    else:
        # if user is logged in, return a list of restaurants that are able to
        # be edited by an authorized user.
        return render_template('restaurants.html',
                               restaurants=restaurants,
                               u=getUserInfo(login_session['user_id']),
                               session=login_session)


@app.route('/restaurant/new', methods=['GET', 'POST'])
def newRestaurant():
    """
    CREATE category route.
    CREATE a category, in this context a restaurant.
    """
    # check if the user is logged in.
    if 'username' not in login_session:
        # redirect to login if not logged in.
        return redirect('/login')
    # check if the method is POST.
    if request.method == 'POST':
        # CREATE a new Restaurant and insert it into the database.
        # Redirect afterwards.
        newRest = Restaurant(name=request.form['name'],
                             user_id=login_session['user_id'])
        session.add(newRest)
        session.commit()
        flash("new restaurant created!")
        return redirect(url_for('showRestaurants'))
    else:
        # on GET return the form to POST.
        return render_template('newrestaurant.html', session=login_session)


@app.route('/restaurant/<int:restaurant_id>/edit', methods=['GET', 'POST'])
def editRestaurant(restaurant_id):
    """
    UPDATE category route.
    In this context categories are restaurants.
    """
    # check if the user is logged in.
    if 'username' not in login_session:
        # redirect to login if not logged in.
        return redirect('/login')
    # get the restaurant to UPDATE
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    # check to see if the current user is authorized to UPDATE the restaurant
    if restaurant.user_id != login_session['user_id']:
        # return an alert chastising the user.
        return """
        <script>
            function unauthAlert() {alert('Current user is not authorized.');}
        </script>
        <body onload='unauthAlert()'>
        """
    # check if the method is POST
    if request.method == 'POST':
        # check if the form has a name and replace the old name with the
        # submitted name. UPDATE the restaurant and redirect.
        if request.form['name']:
            restaurant.name = request.form['name']
        session.add(restaurant)
        session.commit()
        flash("restaurant edited!")
        return redirect(url_for('showRestaurants'))
    else:
        # on GET return the form to POST.
        return render_template('editrestaurant.html',
                               restaurant_id=restaurant_id,
                               restaurant=restaurant,
                               session=login_session)


@app.route('/restaurant/<int:restaurant_id>/delete', methods=['GET', 'POST'])
def deleteRestaurant(restaurant_id):
    """
    DELETE category route.
    In this context deletes a restaurant.
    """
    # check if the user is logged in.
    if 'username' not in login_session:
        # redirect to login if not logged in.
        return redirect('/login')
    # get the restaurant to DELETE
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    # check to see if the current user is authorized to DELETE the restaurant
    if restaurant.user_id != login_session['user_id']:
        # return an alert chastising the user.
        return """
        <script>
            function unauthAlert() {alert('Current user is not authorized.');}
        </script>
        <body onload='unauthAlert()'>
        """
    # check if the method is POST
    if request.method == 'POST':
        # get all items belonging to the restaurant and DELETE them all.
        # then DELETE the restaurant and redirect.
        items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id)
        for item in items:
            session.delete(item)
        session.delete(restaurant)
        session.commit()
        flash("restaurant and menu deleted!")
        return redirect(url_for('showRestaurants'))
    else:
        # on GET return the form to POST.
        return render_template('deleterestaurant.html',
                               restaurant_id=restaurant_id,
                               restaurant=restaurant)


@app.route('/restaurant/<int:restaurant_id>')
@app.route('/restaurant/<int:restaurant_id>/menu')
def showMenu(restaurant_id):
    """
    Item READ route.
    In this context items are menu items.
    """
    # get the restaurant queried for and READ all items belonging to the
    # restaurant.
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant.id)
    # check if user is logged in.
    if ('user_id' not in login_session or
            login_session.get('user_id') != restaurant.user_id):
        # if not logged in return a public menu with a portrait of the creator
        # of the restaurant.
        creator = getUserInfo(restaurant.user_id)
        return render_template('publicmenu.html',
                               restaurant=restaurant,
                               items=items,
                               session=login_session,
                               creator=creator)
    else:
        # if user is logged in, return a menu that is able to
        # be edited by an authorized user.
        return render_template('menu.html',
                               restaurant=restaurant,
                               items=items,
                               session=login_session)


@app.route('/restaurant/<int:restaurant_id>/menu/new', methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
    """
    CREATE item route.
    in this context a menu item.
    """
    # check if the user is logged in.
    if 'username' not in login_session:
        # redirect to login if not logged in.
        return redirect('/login')
    # check if the method is POST.
    if request.method == 'POST':
        # get the restaurant the new item belongs to, and then populate a new
        # item with submitted form fields. Insert the new item into the
        # database and redirect.
        restaurant = session.query(Restaurant).filter_by(
                     id=restaurant_id).one()
        newItem = MenuItem(name=request.form['name'],
                           description=request.form['description'],
                           course=request.form['course'],
                           price=request.form['price'],
                           restaurant_id=restaurant_id,
                           user_id=restaurant.user_id)
        session.add(newItem)
        session.commit()
        flash("new menu item created!")
        return redirect(url_for('showMenu',
                                restaurant_id=restaurant_id))
    else:
        # on GET return the form to POST.
        return render_template('newmenuitem.html',
                               restaurant_id=restaurant_id,
                               session=login_session)


@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit',
           methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
    """
    UPDATE item route.
    In this context items are menu items.
    """
    # check if the user is logged in.
    if 'username' not in login_session:
        return redirect('/login')
    # get the item to UPDATE
    editedItem = session.query(MenuItem).filter_by(id=menu_id).one()
    # check to see if the current user is authorized to UPDATE the item
    if editedItem.user_id != login_session['user_id']:
        # return an alert chastising the user.
        return """
        <script>
            function unauthAlert() {alert('Current user is not authorized.');}
        </script>
        <body onload='unauthAlert()'>
        """
    # check if the method is POST
    if request.method == 'POST':
        # check for edited fields and UPDATE the item accordingly. commit and
        # redirect afterwards.
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['course']:
            editedItem.course = request.form['course']
        if request.form['price']:
            editedItem.price = request.form['price']
        session.add(editedItem)
        session.commit()
        flash("menu item edited!")
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        # on GET return the form to POST.
        return render_template('editmenuitem.html',
                               restaurant_id=restaurant_id,
                               menu_id=menu_id,
                               item=editedItem,
                               session=login_session)


@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete',
           methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    """
    DELETE item route.
    In this context items are menu items.
    """
    # check if the user is logged in.
    if 'username' not in login_session:
        # redirect to login if not logged in.
        return redirect('/login')
    # get the item to DELETE
    item = session.query(MenuItem).filter_by(id=menu_id).one()
    # check to see if the current user is authorized to DELETE the restaurant
    if item.user_id != login_session['user_id']:
        # return an alert chastising the user.
        return """
        <script>
            function unauthAlert() {alert('Current user is not authorized.');}
        </script>
        <body onload='unauthAlert()'>
        """
    # check if the method is POST
    if request.method == 'POST':
        # DELETE the item and redirect.
        session.delete(item)
        session.commit()
        flash("menu item deleted!")
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        # on GET return the form to POST.
        return render_template('deletemenuitem.html',
                               restaurant_id=restaurant_id,
                               item=item,
                               session=login_session)


@app.route('/restaurant/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    """
    JSON endpoint for all items under a category,
    in this context the menu items of a specified restaurant.

    Gets the specified restaurant by id, then gets all items belonging to the
    restaurant and returns a JSON object representing the menu.
    """
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant.id)\
        .all()
    return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    """
    JSON endpoint for a specific item, in this context a menu item.

    Gets a specified item and returns a JSON object representing the item.
    """
    item = session.query(MenuItem).filter_by(id=menu_id).one()
    return jsonify(MenuItem=item.serialize)


@app.route('/restaurants/JSON')
def restaurantJSON():
    """
    JSON endpoint for a list of categories,
    in this context a list of restaurants.

    Gets a list of restaurants, then returns a JSON object
    representing the list of restaurants.
    """
    restaurants = session.query(Restaurant).all()
    return jsonify(Restaurants=[r.serialize for r in restaurants])


@app.route('/login')
def showLogin():
    """
    Route for login page.

    Creates a random state token for mitigating CSRF attacks,
    then stores the state token in the session and returns the login page.
    """
    state = ''.join(random.choice(string.ascii_uppercase +
                    string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """handler for google oauth2 login"""
    # verify the CSRF state token.
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # get the Google one-time-code from the user.
    code = request.data
    # upgrade the code to the user's credentials.
    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.', 401))
        response.headers['Content-Type'] = 'application/json'
        return response

    # get the user's access_token
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # check for a general error
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response
    # check if the recieved user if matches.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response.make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # check if the recieved client id matches this app's
    if result['issued_to'] != G_CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's"), 401)
        print "Token's client ID doe not match app's"
        response.headers['Content-Type'] = 'application/json'
        return response
    # check if the user isn't already logged in.
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if (stored_access_token is not None and gplus_id == stored_gplus_id):
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    # all checks passed, begin login.
    login_session['provider'] = 'google'
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    # ask google for user's info.
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = json.loads(answer.text)
    # write the user to the session.
    login_session['username'] = data["name"]
    login_session['picture'] = data["picture"]
    login_session['email'] = data["email"]
    # check if the user is in the database, if not then add them.
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    # login successful, notify the user.
    output = ''
    output += '<h1>Welcome, %s' % login_session['username']
    output += '!<br>User ID is %d' % login_session['user_id']
    output += '</h1><img src="%s' % login_session['picture']
    output += """
     " style = "width: 300px;
                height: 300px;
                border-radius: 150px;
                -webkit-border-radius: 150px;
                -moz-border-radius: 150px;">
    """
    flash("you are now logged in as %s" % login_session['username'])
    return output


@app.route("/fbconnect", methods=['POST'])
def fbconnect():
    """handler for facebook oauth2 login"""
    # verify the CSRF state token.
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # get the Facebook access token from the user.
    access_token = request.data
    # upgrade the access token.
    fb_client_secrets = json.loads(open('fb_client_secrets.json', 'r').read())
    app_id = fb_client_secrets['web']['app_id']
    app_secret = fb_client_secrets['web']['app_secret']
    url = ('https://graph.facebook.com/oauth/access_token?' +
           ('grant_type=fb_exchange_token&client_id=%s' % app_id) +
           ('&client_secret=%s' % app_secret) +
           ('&fb_exchange_token=%s' % access_token))
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    userinfo_url = "https://graph.facebook.com/v2.4/me"
    token = result.split('&')[0]
    # use upgraded token to get user's info.
    url = userinfo_url + '?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    # begin writing the user to the session.
    login_session['provider'] = 'facebook'
    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['facebook_id'] = data['id']
    # store the access token to log out the user later.
    stored_token = token.split('=')[1]
    login_session['access_token'] = stored_token
    # get the user's portrait.
    url = userinfo_url + '/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['picture'] = data['data']['url']
    # check if the user is in the database, if not then add them.
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    # login successful, notify the user.
    output = ''
    output += '<h1>Welcome, %s' % login_session['username']
    output += '!<br>User ID is %d' % login_session['user_id']
    output += '</h1><img src="%s"' % login_session['picture']
    output += ' class="portrait">'
    flash("you are now logged in as %s" % login_session['username'])
    return output


def fbdisconnect():
    """
    Disconnect method for Facebook logins.

    Gets the relevant information and creates a url. Sends an http request to
    the url to disconnect.
    """
    facebook_id = login_session['facebook_id']
    access_token = login_session['access_token']
    url = (('https://graph.facebook.com/%s' % facebook_id) +
           ('/permissions?access_token=%s' % access_token))
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]


def gdisconnect():
    """
    Disconnect method for Google logins.

    Gets the relevant information and creates a url. Sends an http request to
    the url to disconnect.
    """
    access_token = login_session['access_token']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]


@app.route('/disconnect')
def disconnect():
    """general disconnect route."""
    # check to see if the user is logged in.
    if 'provider' in login_session:
        # check to see if user is logged in with google.
        if login_session['provider'] == 'google':
            # logout with Google and delete Google specific information.
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        # check to see if user is logged in with Facebook.
        if login_session['provider'] == 'facebook':
            # logout with Facebook and delete Facebook specific information.
            fbdisconnect()
            del login_session['facebook_id']
        # delete general user information and return a redirect
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have been logged out.")
        return redirect(url_for('showRestaurants'))
    else:
        # user isn't logged in, redirect them away.
        flash("ERROR: Not logged in.")
        redirect(url_for('showRestaurants'))


def createUser(login_session):
    """
    Helper method for adding a user to the database.

    Collect the user's information into a User object, then adds it to the
    database, then returns the new user's id.
    """
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    """Helper method for getting a user from the database."""
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    """
    Helper method for finding a user's id based on their email. If user does
    not exist, returns None, otherwise returns the user's id.
    """
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# runs the server
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
