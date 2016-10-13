from main import route, BaseHandler

@route(r'/')
class HelloWorld(BaseHandler):

    def get(self):

        """
        get value by key
        """

        self.rd.set('123','321')
        print(self.rd.get('123'))

        self.db.Test.insert({'test': 'test'})
        print self.db.Test.find_one({'test': 'test'})

        return self.write_json({
            'errcode': 0,
            'msg': 'success',
        })
