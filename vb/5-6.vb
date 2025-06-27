Dim polepitch As Integer, slotperpolephase As Single, coilpitchfactor As Single
Dim distributionfactor As Single, windingfactor As Single, ka As Single, mmfofarmature As Single
Dim mmfofarmaturetofieldcurrent As Single, impedance As Single, delta1 As Single, delta As Single, alpha As Single
Dim impedancevoltage As Single, emfofarmature As Single
Dim fieldcurrent() As Single, armaturevoltage() As Single, emffieldcurrent As Single
Dim i0i As Integer
Dim fnumq As Single, gen1 As Single '由功率的到的电流平均值
'***********************************************************
'*    以下是利用计算方法对发电机转子匝间短路的故障诊断      *
'***********************************************************
   n1(14) = 42 '54
   n1(15) = 0.00174 '定子绕组直流电阻
   n1(19) = 18 '节距
   n1(5) = 0.24 '定子绕组漏抗（标么）
   n1(6) = 0.6667 '转子每极嵌放绕组部分与极距之比
   n1(7) = 50 '转子绕组匝数
   n1(8) = 7 ''定子绕组每极每相匝数
   'genmon(5) = 37.541
   'genmon(6) = 459.605
  ' genmon(9) = 3094.316
   'genmon(7) = 21783.919
    If xuanhao = "#5" Then
       n1(7) = 52
    ElseIf xuanhao = "#6" Then
       n1(7) = 52
    End If
    't
     polepitch = n1(14) / 2
    'q
    slotperpolephase = n1(8)
    'ky
    coilpitchfactor = Sin(n1(19) * 1.5707963 / polepitch)
    'kq
    distributionfactor = 0.5 / (slotperpolephase * Sin(0.52359877 / slotperpolephase))
    'kw
    windingfactor = coilpitchfactor * distributionfactor
    'ka
    ka = 9.8696 * n1(6) / (8 * Sin(n1(6) * 1.5707963))
    
   
            If genmon(6) = 0 Then
                    genmon(6) = 100
                
             End If
             If genmon(7) = 0 Then
                 genmon(7) = 22 * 1000
              End If
             
        'Next i0i
        fnumq = Atn(genmon(5) / genmon(6))  '功率因数角
    
    'Fa
     gen1 = (Sqr(genmon(5) ^ 2 + genmon(6) ^ 2) / Sqr(3) / genmon(7)) * 1000 ^ 2  '电枢电流采用PQ计算而得
    
    mmfofarmature = 1.35047447 * n1(8) * windingfactor * gen1 / 1
    'Ifa
    mmfofarmaturetofieldcurrent = mmfofarmature * ka / n1(7)
    'AEr
    impedance = Sqr((n1(15)) ^ 2 + (n1(5) * 22000 / 17495 / Sqr(3)) ^ 2)
    '1
    delta = Atn(n1(5) * 22000 / 17495 / Sqr(3) / n1(15)) '角度
    'AE
    impedancevoltage = Sqr(3) * impedance * gen1 '* genmon(1) 'armaturecurrent.Text
    'E
    emfofarmature = Sqr((impedancevoltage * Sin(delta - fnumq)) ^ 2 + (genmon(7) + impedancevoltage * Cos(delta - fnumq)) ^ 2)
    'a
    delta1 = Atn(impedancevoltage * Sin(delta - fnumq) / (genmon(7) + impedancevoltage * Cos(delta - fnumq)))
    '90+a'
    alpha = delta1 + 1.5707963 + fnumq '* 3.1415926 / 180
    
   Dim xishu1 As Single
  
   
    emfofarmature = emfofarmature / 22000 '
     emffieldcurrent = 100 * (0.2890834679456 * emfofarmature ^ 6 - 1.29353979475545 * emfofarmature ^ 5 + 2.3547326873505 * emfofarmature ^ 4 - 2.20513478437746 * emfofarmature ^ 3 + 1.11149253304413 * emfofarmature ^ 2 - 0.27498467972162 * emfofarmature + 0.0283720708748)
    emffieldcurrent = emffieldcurrent * 1798.4
    actualfieldcurrent = Sqr(emffieldcurrent ^ 2 + mmfofarmaturetofieldcurrent ^ 2 - 2 * emffieldcurrent * mmfofarmaturetofieldcurrent * Cos(alpha))
   
     Text1.Text = actualfieldcurrent
    
    If actualfieldcurrent > 0 Then
        panjuzjianjisuan = (genmon(9) - actualfieldcurrent) / actualfieldcurrent
        
       
    ElseIf actualfieldcurrent <= 0 Then
       
    End If