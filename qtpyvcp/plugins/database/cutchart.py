# cutchart.py
# Prints cutting chart

import sqlite3

db = sqlite3.connect('plasma.db')
print("Opened database successfully")

cursor = db.cursor()

cursor = db.execute("SELECT  cutchart.cu_id, cutchart.cu_pierce_ht, machine.ma_name, operation.op_name, consumable.co_name,\
                    material.mt_name, thickness.th_name,gas.ga_name, quality.qu_name\
                    cu_pierce_delay, cu_cut_ht, cu_cut_spd, cu_volts, cu_kerf_width,\
                    cu_thc_delay, cu_plunge_rate, cu_puddle_ht, cu_amps, cu_pressure, measure.me_name\
                    from cutchart\
                    INNER JOIN consumable ON cutchart.cu_co_id = consumable.co_id\
                    INNER JOIN operation ON cutchart.cu_op_id = operation.op_id\
                    INNER JOIN material ON cutchart.cu_mt_id = material.mt_id\
                    INNER JOIN gas ON cutchart.cu_ga_id = gas.ga_id\
                    INNER JOIN quality ON cutchart.cu_qu_id = quality.qu_id\
                    INNER JOIN thickness ON cutchart.cu_th_id = thickness.th_id\
                    INNER JOIN measure ON cutchart.cu_me_id = measure.me_id\
                    INNER JOIN machine ON cutchart.cu_ma_id = machine.ma_id\
                    WHERE cutchart.cu_qu_id = 1;"  # Quality Filter 1 = Best quality, 2 = Production quality
                    )

for row in cursor:
    print("\n")
    print(("Chart ID = ", row[0]))
    print(("Machine Name = ", row[2]))
    print(("Measurement System = ", row[18]))
    print(("Pierce Height = ", row[1]))
    print(("Operation = ", row[3]))
    print(("Consumable = ", row[4]))
    print(("Material = ", row[5]))
    print(("Thickness = ", row[6]))
    print(("Gas = ", row[7]))
    print(("Quality = ", row[8]))
    print(("Cut Height = ", row[9]))
    print(("Cut Speed = ", row[10]))
    print(("Volts = ", row[11]))
    print(("Kerf Width = ", row[12]))
    print(("THC Delay = ", row[13]))
    print(("Plunge Rate = ", row[14]))
    print(("Puddle Jump Height = ", row[15]))
    print(("Amps = ", row[16]))
    print(("Gass Pressure = ", row[17]))

    print("\n")
print("\n")

print("Operation done successfully")
db.close()
