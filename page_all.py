# -*- coding: utf-8 -*-
"""
Created on Sun Jun 25 03:38:11 2017
@author: dc
"""

import http.server as hs
import sys, os
import subprocess


class ServerException(Exception):
    '''服务器内部错误'''

    pass


# 如果路径不存在
class case_no_path(object):
    '''如果路径不存在'''

    def test(self, handler):
        return not os.path.exists(handler.full_path)

    def act(self, handler):
        raise ServerException("{0} not found".format(handler.path))


# 所有情况都不符合时的默认处理类
class case_allother_fail(object):
    '''所有情况都不符合时的默认处理类'''

    def test(self, handler):
        return True

    def act(self, handler):
        raise ServerException("Unknown object {0}".format(handler.full_path))


class case_is_file(object):
    ''' 输入的路径是一个文件'''

    def test(self, handler):
        return os.path.isfile(handler.full_path)

    def act(self, handler):
        handler.handle_file(handler.full_path)


class case_CGI_file(object):

    def test(self, handler):
        print(os.path.isfile(handler.full_path) and handler.full_path.endswith('.py'))
        return os.path.isfile(handler.full_path) and \
               handler.full_path.endswith('.py')

    def act(self, handler):
        handler.run_cgi(handler.full_path)


class case_index_file(object):
    '''输入跟url时显示index.html'''

    def index_path(self, handler):
        return os.path.join(handler.full_path, 'index.html')

    # 判断目标路径是否是目录，且需要判断目录下是否包含index.html
    def test(self, handler):
        return os.path.isdir(handler.full_path) and \
               os.path.isfile(self.index_path(handler))

    def act(self, handler):
        handler.handle_file(self.index_path(handler))


class RequestHandler(hs.BaseHTTPRequestHandler):
    '''
    请求路径合法则返回相应处理，
    否则返回错误页面
    '''

    full_path = ""

    # 一定要注意条件类的优先顺序不同，对于文件的捕捉能力也不同，越是针对某种特例的条件类，
    # 越应该放在前面。
    cases = [case_no_path(),
             case_CGI_file(),
             case_is_file(),
             case_index_file(),
             case_allother_fail()]

    def run_cgi(self, fullpath):

        # 运行cgi脚本并得到格式化的输出，从而可以显示到浏览器上
        data = subprocess.check_output(["python", fullpath])

        # self.wfile.write(bytes(fullpath, encoding = 'utf-8'))

        self.send_content(page=str(data, encoding='utf-8'))

    def send_content(self, page, status=200):

        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(bytes(page, encoding='utf-8'))
        # print(page)

    def do_GET(self):
        # 这里要处理两个异常，一个是读入路径时可能出现的异常，一个是读入路径后若不是文件，要作为异常处理
        try:

            # 获取文件路径
            self.full_path = os.getcwd() + self.path

            # 如果路径不存在
            for case in self.cases:

                if case.test(self):
                    case.act(self)

                    break

        except Exception as msg:

            self.handle_error(msg)

    def handle_file(self, full_path):

        try:

            with open(full_path, 'r') as file:

                content = file.read()

            self.send_content(content, 200)

        except IOError as msg:

            msg = "'{0}' cannot be read: {1}".format(self.path, msg)

            self.handle_error(msg)

    Error_Page = """\
    <html>
    <body>
    <h1>Error accessing {path}</h1>
    <p>{msg}</p>
    </body>
    </html>
    """

    def handle_error(self, msg):

        content = self.Error_Page.format(path=self.path, msg=msg)

        self.send_content(content, 404)


if __name__ == '__main__':
    httpAddress = ('', 8090)

    httpd = hs.HTTPServer(httpAddress, RequestHandler)

    httpd.serve_forever()