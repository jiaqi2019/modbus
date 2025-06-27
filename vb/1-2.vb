Private Sub Command2_Click()
On Error Resume Next
Dim polepitch As Integer, slotperpolephase As Single, coilpitchfactor As Single
Dim distributionfactor As Single, windingfactor As Single, ka As Single, mmfofarmature As Single
Dim mmfofarmaturetofieldcurrent As Single, impedance As Single, delta1 As Single, delta As Single, alpha As Single
Dim impedancevoltage As Single, emfofarmature As Single
Dim fieldcurrent() As Single, armaturevoltage() As Single, emffieldcurrent As Single
Dim i0i As Integer
Dim fnumq As Single, gen1 As Single
'***********************************************************
'*    以下是利用计算方法对1、2号发电机转子匝间短路的故障判据      *
'***********************************************************
     
   '采集发电机运行量，Q\P\If\ UA
   genmon(5) = 83.067
   genmon(6) = 550.023
   genmon(9) = 3032.161
   genmon(7) = 21569
     
     
  '1，2发电机参数
   n1(14) = 42 '54
   n1(15) = 0.00154 '定子绕组直流电阻
   n1(19) = 18 '节距
   n1(5) = 0.135 '定子绕组漏抗（标么）
   n1(6) = 0.666667 '转子每极嵌放绕组部分与极距之比
   n1(7) = 56 '转子绕组匝数
   n1(8) = 7 ''定子绕组每极每相匝数
   
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
             
         fnumq = Atn(genmon(5) / genmon(6))  '功率因数角
         'Fa
     gen1 = (Sqr(genmon(5) ^ 2 + genmon(6) ^ 2) / Sqr(3) / genmon(7)) * 1000 ^ 2  '电枢电流采用PQ计算而得
    
    mmfofarmature = 1.35047447 * n1(8) * windingfactor * gen1 / 1
    'Ifa
    mmfofarmaturetofieldcurrent = mmfofarmature * ka / n1(7)
    'AEr
    impedance = Sqr((n1(15)) ^ 2 + (n1(5) * 22000 / 17583 / Sqr(3)) ^ 2)
    '1
    delta = Atn(n1(5) * 22000 / 17583 / Sqr(3) / n1(15)) '角度
    'AE
    impedancevoltage = Sqr(3) * impedance * gen1
    'E
    emfofarmature = Sqr((impedancevoltage * Sin(delta - fnumq)) ^ 2 + (genmon(7) + impedancevoltage * Cos(delta - fnumq)) ^ 2)
    'a
    delta1 = Atn(impedancevoltage * Sin(delta - fnumq) / (genmon(7) + impedancevoltage * Cos(delta - fnumq)))
    '90+a'
    alpha = delta1 + 1.5707963 + fnumq
    
    emfofarmature = emfofarmature / 10
   
     emffieldcurrent = 0.0000000007273 * emfofarmature ^ 4 - 0.000004801 * emfofarmature ^ 3 + 0.01191 * emfofarmature ^ 2 - 12.41 * emfofarmature + 5300
   
   '正常励磁电流计算
    actualfieldcurrent = Sqr(emffieldcurrent ^ 2 + mmfofarmaturetofieldcurrent ^ 2 - 2 * emffieldcurrent * mmfofarmaturetofieldcurrent * Cos(alpha))
   
     Text1.Text = actualfieldcurrent
    
    If actualfieldcurrent > 0 Then
   '匝间短路判据：
        panjuzjianjisuan = (genmon(9) - actualfieldcurrent) / actualfieldcurrent
        
        
    ElseIf actualfieldcurrent <= 0 Then
        'MsgBox "数据错误，请重新采集数据", , "RDST----警示"
        'Exit Sub
    End If

End Sub