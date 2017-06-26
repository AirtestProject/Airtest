from new_test.mock_content import mock_content


class adbmock():
    mockstuff=None
    content_enable={}
    cmd_enable={}
    mock_content=mock_content()

    def __init__(self):
        #self.mockstuff=mock()
        pass
    def set_enable(self,content,status):
        if(status in  [True,False]):
            self.content_enable[content]=status

    def set_cmd_enable(self,content,status):
        if type(status)==int:
            self.cmd_enable[content]=status

    def shell(self,content):
        if content in self.content_enable.keys() and self.content_enable[content]:
            return self.mock_content.shell_dick[content]
        else:
            return ""

    # for cmd method
    def cmd(self, cmds, device=True):
        if cmds in self.cmd_enable.keys() and self.cmd_enable[cmds] in self.mock_content.cmd_dick[cmds].keys() :
            num=self.cmd_enable[cmds]
            return self.mock_content.cmd_dick[cmds][num]
        else:
            return ""
