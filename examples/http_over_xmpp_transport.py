from sleekxmpp import ClientXMPP
import logging


# def tracefunc(frame, event, arg, indent=[0]):
#     prefix = "/Users/sangeeth/code/SleekXMPP/sleekxmpp/"
#     if not frame.f_code.co_filename.startswith(prefix):
#         return tracefunc
#     if event == "call":
#         indent[0] += 2
#         cn = getattr(
#             getattr(frame.f_locals.get("self"), "__class__", None),
#             "__name__", None
#         )
#         print "{}{} {} {}".format(
#             "." * indent[0], frame.f_code.co_filename[len(prefix):],
#             cn, frame.f_code.co_name
#         )
#     elif event == "return":
#         indent[0] -= 2
#     return tracefunc
#
#
# import sys
# sys.settrace(tracefunc)


class HTTPOverXMPPClient(ClientXMPP):
    def __init__(self, jid, password):
        ClientXMPP.__init__(self, jid, password)

    #     self.register_plugin('xep_0030')  # Service Discovery
    #     self.register_plugin('xep_0004')  # Data Forms
    #     self.register_plugin('xep_0060')  # PubSub
    #     self.register_plugin('xep_0199')  # XMPP Ping
    #
    #     self.add_event_handler("session_start", self.session_start)
    #     self.add_event_handler("connected", self.connected)
    #
    # def session_start(self, event):
    #     print "Client::session_start()"
    #     self.send_presence()
    #     print self.get_roster()
    #
    # def connected(self, event):
    #     print "Client::connected()"


def get_cred(filename="/tmp/.cred"):
    with open(filename, "r") as f:
        return f.readline().split()


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.DEBUG, format='%(levelname)-8s %(message)s'
    )

    jid, password = get_cred()
    xmpp = HTTPOverXMPPClient(jid, password)
    if xmpp.connect(("talk.l.google.com", 5222)):
        print "Connected!"
        xmpp.process(block=True)
    else:
        print "Not connected!"
    print "Goodbye...."


