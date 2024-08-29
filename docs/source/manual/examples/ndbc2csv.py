import glob
import os
import pandas as pd
import cht_utils.misc_tools
import numpy as np

stations = ['41043', '41044', '41046', '41047', '41049', '41052', '42059', '42060', '42085']

path = r"\cosmos\observations\hurricane_fiona\waves"

for i,v in enumerate(stations):

        files = glob.glob(os.path.join(path, v + "*"))

        for ii, vv in enumerate(files):

                df = pd.read_csv(vv, header=[0,1], index_col=None,
                        delim_whitespace=True) 

                Hs= df.WVHT.values[:,0]
                Tp= df.DPD.values[:,0]
                MWD= df.MWD.values[:,0]

                ind= np.argwhere(Hs!=99)[:,0]
                df2 = pd.DataFrame({'year': df.values[ind,0], 'month':  df.values[ind,1], 'day':  df.values[ind,2],'hour':  df.values[ind,3], 'minute':  df.values[ind,4]})
                dates = pd.to_datetime(df2)
                if ii==0:
                        df4= pd.DataFrame({'date': dates, 'hs':  Hs[ind], 'tp':  Tp[ind]}, index=None)
                else:
                        df4= df4.append(pd.DataFrame({'date': dates, 'hs':  Hs[ind], 'tp':  Tp[ind]}, index=None), ignore_index=True)
        df4.sort_values(by='date', inplace = True)
        s = df4.to_csv(date_format='%Y-%m-%dT%H:%M:%S',
                                                float_format='%.3f',
                                                header=False, index=False, line_terminator='\r\n')            


        csv_file = os.path.join(path, "waves." + stations[i] + ".observed.csv.js")
        cht_utils.misc_tools.write_csv_js(csv_file, s, "var csv = `date_time,hm0,tp")
    