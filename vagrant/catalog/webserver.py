from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi

from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Restaurant, MenuItem

engine = create_engine('sqlite:///restaurantmenu.db')

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


class webserverHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path.endswith("/edit"):
                restaurantIDPath = self.path.split('/')[2]
                restaurantQuery = session.query(Restaurant)\
                    .filter_by(id=restaurantIDPath).one()
                if restaurantQuery != []:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()

                    output = "<html><body>"
                    output += "<h1>%s</h1><br>" % restaurantQuery.name
                    output += "<form method='POST' enctype='multipart/form-da"\
                        "ta' action='/restaurants/%s/edit'>" % restaurantIDPath
                    output += "<input name='name' type='text'><input type='su"\
                              "bmit' value='Rename'></form>"
                    output += "</body></html>"

                    self.wfile.write(output)
                    print output
                    return

            if self.path.endswith("/delete"):
                restaurantIDPath = self.path.split('/')[2]
                restaurantQuery = session.query(Restaurant)\
                    .filter_by(id=restaurantIDPath).one()
                if restaurantQuery != []:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()

                    output = "<html><body>"
                    output += "<h1>Are you sure you want to delete %s?</h1>"\
                              % restaurantQuery.name
                    output += "<form method='POST' enctype='multipart/form-da"\
                              "ta' action='/restaurants/%s/delete'>"\
                              % restaurantIDPath
                    output += "<input type='submit' value='Delete'></form>"
                    output += "</body></html>"

                    self.wfile.write(output)
                    print output
                    return

            if self.path.endswith("/restaurants/new"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                output = "<html><body>"
                output += "<h1>Make a New Restaurant</h1><br>"
                output += "<form method='POST' enctype='multipart/form-data' "\
                          "action='/restaurants/new'><input name='name' "\
                          "type='text'><input type='submit' value='Creat"\
                          "e'></form>"
                output += "</body></html>"

                self.wfile.write(output)
                print output
                return

            if self.path.endswith("/restaurants"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                output = "<html><body><a href='/restaurants/new'>Make a new r"\
                         "estaurant</a><ul>"
                query = session.query(Restaurant).all()
                for restaurant in query:
                    output += "<li> %s <a href='/restaurants/%d/edit'>edit</a"\
                         "> <a href='/restaurants/%d/delete'>delete</a></li>" \
                              % (restaurant.name, restaurant.id, restaurant.id)

                output += "</ul></body></html>"
                self.wfile.write(output)
                print output
                session.close()
                return

            if self.path.endswith("/hello"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                output = ""
                output += "<html><body>Hello!"
                output += "<form method='POST' enctype='multipart/form-data' "\
                          "action='/hello'><h2>What would you like me to say?"\
                          "</h2><input name='message' type='text'><input "\
                          "type='submit' value='Submit'></form>"
                output += "</body></html>"
                self.wfile.write(output)
                print output
                return

            if self.path.endswith("/hola"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                output = ""
                output += "<html><body>&#161hola! <a href='/hello'>Back to " \
                          "Hello</a>"
                output += "<form method='POST' enctype='multipart/form-data' "\
                          "action='/hello'><h2>What would you like me to say?"\
                          "</h2><input name='message' type='text'><input "\
                          "type='submit' value='Submit'></form>"
                output += "</body></html>"
                self.wfile.write(output)
                print output
                return

        except IOError:
            self.send_error(404, "File Not Found %s" % self.path)

    def do_POST(self):
        try:
            if self.path.endswith("/hello"):
                self.send_response(301)
                self.end_headers()

                ctype, pdict = cgi.parse_header(self.headers
                                                .getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    messagecontent = fields.get('message')

                output = ""
                output += "<html><body>"
                output += " <h2> Okay, how about this: </h2>"
                output += "<h1> %s </h1>" % messagecontent[0]

                output += "<form method='POST' enctype='multipart/form-data' "\
                          "action='/hello'><h2>What would you like me to say?"\
                          "</h2><input name='message' type='text'><input "\
                          "type='submit' value='Submit'></form>"
                output += "</body></html>"
                self.wfile.write(output)
                print output
                return

            if self.path.endswith("/restaurants/new"):
                self.send_response(301)
                self.send_header('Location', '/restaurants')
                self.end_headers()

                ctype, pdict = cgi.parse_header(self.headers
                                                .getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    restaurant_name = fields.get('name')[0]

                restaurant = Restaurant(name=str(restaurant_name))
                session.add(restaurant)
                session.commit()
                return

            if self.path.endswith("/edit"):
                restaurantIDPath = self.path.split('/')[2]
                restaurantQuery = session.query(Restaurant)\
                    .filter_by(id=restaurantIDPath).one()
                if restaurantQuery != []:
                    self.send_response(301)
                    self.send_header('Location', '/restaurants')
                    self.end_headers()

                    ctype, pdict = cgi.parse_header(self.headers
                                                    .getheader('content-type'))
                    if ctype == 'multipart/form-data':
                        fields = cgi.parse_multipart(self.rfile, pdict)
                        restaurant_name = fields.get('name')[0]

                    restaurantQuery.name = restaurant_name
                    session.add(restaurantQuery)
                    session.commit()
                    return

            if self.path.endswith("/delete"):
                restaurantIDPath = self.path.split('/')[2]
                restaurantQuery = session.query(Restaurant)\
                    .filter_by(id=restaurantIDPath).one()
                if restaurantQuery != []:
                    self.send_response(301)
                    self.send_header('Location', '/restaurants')
                    self.end_headers()

                    session.delete(restaurantQuery)
                    session.commit()
                    return

        except:
            pass


def main():
    try:
        port = 8080
        server = HTTPServer(('', port), webserverHandler)
        print "Web server running on port %s" % port
        server.serve_forever()

    except KeyboardInterrupt:
        print "^C entered, stopping web server..."
        server.socket.close()


if __name__ == '__main__':
    main()
