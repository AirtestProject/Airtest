# encoding=utf-8

# 在stf-web个人设置页的“Setting UI”——“密钥”——“访问令牌”生成的，需要自行纪录一下
# 密钥和节点是一一对应的，用别人的密钥会导致连接不上设备
STF_TOKEN_ID = '0bdfdb70533d415ba2781c0dff47c3c5528d23a0dac44e81882cb2874c37ce3e'


# 安装之前会先清掉第三方应用
# 这里是不清掉的列表
PKG_NOT_REMOVE = [
    "com.netease.accessibility",
    "com.netease.releaselock",
    "com.tencent.mm",
]


# MTL提供的稳定设备列表
TEST_DEVICE_LIST = (
    '07173333',
    'QLXBBBA5B1137702',
    'JTJ4C15710038858',
    'T3Q4C15B04019605',
    '96528427',
    '1197d597',
    '4c6a4cf2',
    '351BBJPTHLR2',
    '351BBJPZ8F27',
    '351BBJPYF7PF',
    '88MFBM72H9SN',
    '810EBM535P6F',
    'BH904FXV16',
    'CB5A21QQEN',
    '4a139669',
    'T7G5T15730003758',
    'DU2SSE15CA048623',
    'DU2SSE149G047150',
    '71MBBLA238NH',
    '4df74f4b47e33081',
    'eebcdab5',
    '7N2SQL151N004298',
    'G2W7N15930015071',
    'G1NPCX069194A8V',
    '4e49701b'
)