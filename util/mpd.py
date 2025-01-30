# MPD 工具
import re
from lxml import etree
from route.consts.url_type import accept_content_type_regex_list_mpd


class XMLFile:
    """
    XML 文件
    """

    def __init__(self,
                 content: str,
                 content_type: str = None):
        """
        初始化
        :param content: 待转化的 XML 文本
        :param find_xml_declaration: 是否寻找 xml 的头部信息
        :param content_type: 请求此文件响应的 Content-Type
        """
        self.declaration = None
        self.content_type = content_type
        self.root = etree.fromstring(content.encode('utf-8'))
        self.namespace = ""

        # 处理 root 标签名和命名空间
        self.root_tag_name = self.root.tag
        if '}' in self.root.tag:
            self.namespace = '{' + self.root.tag.split('}', 1)[0][1:] + "}"  # 提取命名空间
            self.root_tag_name = self.root.tag.split('}', 1)[1]  # 提取标签名

    def get_element(self, path: str):
        """
        获取元素
        :param path: 路径
        :return: 返回查找到的元素，不存在返回 None
        """
        return self.root.find('/'.join([self.namespace + path for path in path.split('/')]))

    def get_element_text(self, path: str) -> str:
        """
        获取元素的值
        :param path: 路径
        :return: 返回查找到的元素的 text，不存在元素返回 None
        """
        text = None
        element = self.get_element(path)

        if element is not None:
            text = element.text

        return text

    def insert_or_update_value(self, path: str, value: str):
        """
        新增或删除某个元素
        :param path: 路径
        :param value: 文本值
        """
        paths = path.split('/')
        now_element = self.root

        for element_tag_name in paths:
            element_tag_name = self.namespace + element_tag_name
            next_element = now_element.find(element_tag_name)
            if next_element is None:
                # 当前级别没有元素，新建一个
                next_element = etree.Element(element_tag_name)
                now_element.append(next_element)

            # 赋值
            now_element = next_element

        # 插入值
        now_element.text = value

    def get_xml_content(self):
        return etree.tostring(self.root,
                              pretty_print=True,
                              xml_declaration=True,
                              encoding='UTF-8').decode()

    def is_mpd_file(self) -> bool:
        """
        判断文件是否是 MPD 文件
        """
        if self.root_tag_name == 'MPD':
            period = self.root.find(f'{self.namespace}Period')
            if period is not None:
                # 是 MPD 文件
                return True

        if self.content_type is not None:
            # 判断 Content-Type 是否是合法的
            for regex in accept_content_type_regex_list_mpd:
                if re.fullmatch(regex, self.content_type):
                    # Content-Type 合法
                    return True

        # 不是 MPD 文件
        return False
