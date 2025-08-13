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
       n1(14) = 60 '54
   n1(15) = 0.00192 '定子绕组直流电阻
   n1(19) = 25 '节距
   n1(5) = 0.1195 '定子绕组漏抗（标么）
   n1(6) = 0.6667 '转子每极嵌放绕组部分与极距之比
   n1(7) = 88 '转子绕组匝数
   n1(8) = 10 ''定子绕组每极每相匝数
   'genmon(5) = 38.17
   'genmon(6) = 128.94
   'genmon(9) = 1098.42
  ' genmon(7) = 19490
      
    
    If xuanhao = "#11" Then
       n1(7) = 88
    ElseIf xuanhao = "#12" Then
       n1(7) = 88
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
    
    'For q = 12 To 0 Step -1
        'For i0i = 1 To 8
            If genmon(6) = 0 Then
                    genmon(6) = 100
                'MsgBox ("数据采集不正确")
                'Print genmon(i0i)
                'Print genmon(6)
                'MsgBox "数据错误，请重新采集数据", , "RDST----警示"
                'Unload zajianduanlu
                'End
             End If
             If genmon(7) = 0 Then
                 genmon(7) = 22 * 1000
              End If
             
        'Next i0i
        fnumq = Atn(genmon(5) / genmon(6))  '功率因数角
      'For z = 11000 To 1000 Step -10
    'Fa
     gen1 = (Sqr(genmon(5) ^ 2 + genmon(6) ^ 2) / Sqr(3) / genmon(7)) * 1000 ^ 2  '电枢电流采用PQ计算而得
    
    mmfofarmature = 1.35047447 * n1(8) * windingfactor * gen1 / 1
    'Ifa
    mmfofarmaturetofieldcurrent = mmfofarmature * ka / n1(7)
    'AEr
      impedance = Sqr((n1(15)) ^ 2 + (n1(5) * 20000 / 10190 / Sqr(3)) ^ 2)
    '1
    delta = Atn(n1(5) * 20000 / 10190 / Sqr(3) / n1(15)) '角度
    'AE
    impedancevoltage = Sqr(3) * impedance * gen1 '* genmon(1) 'armaturecurrent.Text
    'E
    emfofarmature = Sqr((impedancevoltage * Sin(delta - fnumq)) ^ 2 + (genmon(7) + impedancevoltage * Cos(delta - fnumq)) ^ 2)
    'a
    delta1 = Atn(impedancevoltage * Sin(delta - fnumq) / (genmon(7) + impedancevoltage * Cos(delta - fnumq)))
    '90+a'
    alpha = delta1 + 1.5707963 + fnumq

  emfofarmature = emfofarmature / 100
  emffieldcurrent = 4.32638 * 10 ^ -10 * emfofarmature ^ 6 - 4.09765104 * 10 ^ -7 * emfofarmature ^ 5 + 1.547534903 * 10 ^ -4 * emfofarmature ^ 4 - 2.8793655254652 * 10 ^ -2 * emfofarmature ^ 3 + 2.6201859638555 * emfofarmature ^ 2 - 89.0634841496725 * emfofarmature - 0.000089855825792
 
    
    actualfieldcurrent = Sqr(emffieldcurrent ^ 2 + mmfofarmaturetofieldcurrent ^ 2 - 2 * emffieldcurrent * mmfofarmaturetofieldcurrent * Cos(alpha))
    
     Text1.Text = actualfieldcurrent
    
    If actualfieldcurrent > 0 Then
        panjuzjianjisuan = (genmon(9) - actualfieldcurrent) / actualfieldcurrent
        
      
    ElseIf actualfieldcurrent <= 0 Then
        'MsgBox "数据错误，请重新采集数据", , "RDST----警示"
        'Exit Sub
    End If