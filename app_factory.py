import cgi
import uwsgi_hello
import env_test 

known_apps = { 
    'hello_world': uwsgi_hello.UwsgiHello,
    'env_test': env_test.EnvTest,
}


def application(environ, start_response):
    path = environ['PATH_INFO']

    path_parts = path.split('/')

    log = environ['wsgi.errors']

    for k, v in known_apps.iteritems():
        if k in path_parts:
            print >> log, 'Running requested app ' + k
            return v(environ, start_response).application()

    #if 'hello_world' in path_parts:
    #    print >> log, "Running requested app hello_world"
    #    return uwsgi_hello.application(environ, start_response)
    #if 'env_test' in path_parts:
    #    print >> log, "Running requested app env_test"
    #    return env_test.application(environ, start_response)

    # Sorting and stringifying the environment key, value pairs
    response_body = 'You wanted to get to ' + cgi.escape(path) + ' That is an unknown application'

    status = '501 Not implemented'
    response_headers = [('Content-Type', 'text/plain'),
                    ('Content-Length', str(len(response_body)))]
    start_response(status, response_headers)

    return [response_body]