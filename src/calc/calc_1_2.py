import math

def calculate(genmon):
    """
    计算1号和2号发电机的励磁电流和比值
    参数:
        genmon: 发电机监测值列表 [Q, P, If, UA]
    返回:
        tuple: (计算得到的励磁电流, 励磁电流比值)
    """
    # 发电机参数
    n1 = {
        14: 42,  # 极距
        15: 0.00154,  # 定子绕组直流电阻
        19: 18,  # 节距
        5: 0.135,  # 定子绕组漏抗（标么值）
        6: 0.666667,  # 转子每极嵌放绕组部分与极距之比
        7: 56,  # 转子绕组匝数
        8: 7  # 定子绕组每极每相匝数
    }

    # 提取监测值
    reactive_power = genmon[5]  # 无功功率
    active_power = genmon[6]    # 有功功率
    excitation_current = genmon[9]  # 励磁电流
    line_voltage = genmon[7]    # 线电压

    # 处理零值
    if active_power == 0:
        active_power = 100
    if line_voltage == 0:
        line_voltage = 22000

    # 计算参数
    polepitch = n1[14] / 2  # 极距
    slotperpolephase = n1[8]  # 每极每相槽数
    coilpitchfactor = math.sin(n1[19] * math.pi/2 / polepitch)  # 节距系数
    distributionfactor = 0.5 / (slotperpolephase * math.sin(math.pi/6 / slotperpolephase))  # 分布系数
    windingfactor = coilpitchfactor * distributionfactor  # 绕组系数
    ka = 9.8696 * n1[6] / (8 * math.sin(n1[6] * math.pi/2))  # 系数ka

    # 计算功率因数角
    fnumq = math.atan2(reactive_power, active_power)

    # 计算电枢电流
    gen1 = (math.sqrt(reactive_power**2 + active_power**2) / math.sqrt(3) / line_voltage) * 1000**2

    # 计算电枢磁势
    mmfofarmature = 1.35047447 * n1[8] * windingfactor * gen1
    mmfofarmaturetofieldcurrent = mmfofarmature * ka / n1[7]  # 电枢磁势对应的励磁电流

    # 计算阻抗和角度
    impedance = math.sqrt(n1[15]**2 + (n1[5] * 22000 / 17583 / math.sqrt(3))**2)  # 阻抗
    delta = math.atan2(n1[5] * 22000 / 17583 / math.sqrt(3), n1[15])  # 阻抗角
    impedancevoltage = math.sqrt(3) * impedance * gen1  # 阻抗压降

    # 计算电动势
    emfofarmature = math.sqrt(
        (impedancevoltage * math.sin(delta - fnumq))**2 + 
        (line_voltage + impedancevoltage * math.cos(delta - fnumq))**2
    )
    delta1 = math.atan2(
        impedancevoltage * math.sin(delta - fnumq),
        line_voltage + impedancevoltage * math.cos(delta - fnumq)
    )
    alpha = delta1 + math.pi/2 + fnumq  # 角度alpha

    # 计算励磁电流
    emfofarmature = emfofarmature / 10
    emffieldcurrent = (
        0.0000000007273 * emfofarmature**4 - 
        0.000004801 * emfofarmature**3 + 
        0.01191 * emfofarmature**2 - 
        12.41 * emfofarmature + 
        5300
    )

    # 计算实际励磁电流
    actualfieldcurrent = math.sqrt(
        emffieldcurrent**2 + 
        mmfofarmaturetofieldcurrent**2 - 
        2 * emffieldcurrent * mmfofarmaturetofieldcurrent * math.cos(alpha)
    )
    # print(f"计算得到的励磁电流: {actualfieldcurrent}")
    # 计算励磁电流比值
    if actualfieldcurrent > 0:
        ratio = abs((excitation_current - actualfieldcurrent) / actualfieldcurrent)
    else:
        ratio = 0

    return actualfieldcurrent, ratio 