#encoding=utf8
__author__ = 'Someone'

set_serialno()
# start your script here
#server_call("call at/team/get->atmain(%s,[0])" %UID)
#call cmd/wizcmd->com_cloneobj(uid,"20140 1")
server_call("fight kill")
server_call("call at/hai/close_all_pop->close_all_pop(%s)"%UID)
server_call("call cmd/wizcmd->com_goto(%s,\"101,90,66\")"%UID)
server_call("call task/task_mgr->_X_clearall(%s)"%UID)
