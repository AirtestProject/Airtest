from airtest.core.android.android import Javacap, Android


def test_javacap():
    j = Javacap("BY3AME158C028901", localport=10001)
    # f = j.get_frames()
    # for i in f:
    #     print(len(i), i[:100])
    while True:
        i = j.get_frame()
        print(len(i), i[:100])


def test_javacap_in_android():
    a = Android(minicap=False, javacap=True)
    a.snapshot("test.png")


def test_minicap(): 
    a = Android(minicap=True, javacap=False)
    a.snapshot("test2.png")


if __name__ == '__main__':
    test_javacap_in_android()
    test_minicap()
