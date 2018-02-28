# encoding:utf-8
# Copyright 2012 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

#异常类
class ParseError(Exception):
    def __init__(self, message, lineno, line):
        self.msg = message
        self.line = line
        self.lineno = lineno

    def __str__(self):
        return 'at line %d, %s: %r' % (self.lineno, self.msg, self.line)


#简单的ini文件解析
class BaseParser(object):
    lineno = 0
    #异常处理方式注册
    parse_exc = ParseError

    def _assignment(self, key, value):
        self.assignment(key, value)
        return None, []

    def _get_section(self, line):
        if not line.endswith(']'):
            #section必须以']'结尾
            return self.error_no_section_end_bracket(line)
        if len(line) <= 2:
            return self.error_no_section_name(line)

        #返回section名称
        return line[1:-1]

    #key,value拆分
    def _split_key_value(self, line):
        colon = line.find(':')
        equal = line.find('=')
        if colon < 0 and equal < 0:
            return self.error_invalid_assignment(line)

        if colon < 0 or (equal >= 0 and equal < colon):
            key, value = line[:equal], line[equal + 1:]
        else:
            key, value = line[:colon], line[colon + 1:]

        value = value.strip()
        if value and value[0] == value[-1] and value.startswith(("\"", "'")):
            value = value[1:-1]
        return key.strip(), [value]

    #完成ini文件解析
    def parse(self, lineiter):
        key = None
        value = []

        #遍历文件每一行
        for line in lineiter:
            #增加行号
            self.lineno += 1

            #移除行尾的空字符
            line = line.rstrip()
            if not line:
                # Blank line, ends multi-line values
                #遇到空行，说明上一行的key及value已表述完成
                if key:
                    key, value = self._assignment(key, value)
                continue
            elif line.startswith((' ', '\t')):
                #遇到以' ','\t'开头的行，说明正在继续上一行的赋值，为value添加内容
                # Continuation of previous assignment
                if key is None:
                    #如果没有key，则报错
                    self.error_unexpected_continuation(line)
                else:
                    value.append(line.lstrip())
                continue

            #else 此时遇到的行是一个新的key,value对或者section，先将上次的key,value进行赋值
            if key:
                # Flush previous assignment, if any
                key, value = self._assignment(key, value)

            #遇到section
            if line.startswith('['):
                # Section start
                section = self._get_section(line)
                if section:
                    #新增section
                    self.new_section(section)
            elif line.startswith(('#', ';')):
                #支持'#'号及';'开头的注释行识别
                self.comment(line[1:].lstrip())
            else:
                #合适的key,value对行，将其拆分成key,value
                key, value = self._split_key_value(line)
                if not key:
                    return self.error_empty_key(line)

        #文件到达结尾，flush 最后一个key,value
        if key:
            # Flush previous assignment, if any
            self._assignment(key, value)

    def assignment(self, key, value):
        """Called when a full assignment is parsed."""
        raise NotImplementedError()

    def new_section(self, section):
        """Called when a new section is started."""
        raise NotImplementedError()

    def comment(self, comment):
        """Called when a comment is parsed."""
        pass

    def error_invalid_assignment(self, line):
        raise self.parse_exc("No ':' or '=' found in assignment",
                             self.lineno, line)

    def error_empty_key(self, line):
        raise self.parse_exc('Key cannot be empty', self.lineno, line)

    def error_unexpected_continuation(self, line):
        raise self.parse_exc('Unexpected continuation line',
                             self.lineno, line)

    def error_no_section_end_bracket(self, line):
        raise self.parse_exc('Invalid section (must end with ])',
                             self.lineno, line)

    def error_no_section_name(self, line):
        raise self.parse_exc('Empty section name', self.lineno, line)
