from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs'
def summarize():
    p=OUT/'r03_ksce2023_spectrum_transfer.csv'
    df=pd.read_csv(p)
    threshold=10.0
    df['abs_relative_error_pct']=df['relative_error_pct'].abs()
    s={'source_rows':24,'reconstructed_rows':int(len(df)),'unique_case_ids':int(df.case_id.nunique()),'screen_tolerance_pct':threshold,'rmse_pct':float(np.sqrt(np.mean(df.relative_error_pct**2))),'q95_abs_error_pct':float(np.quantile(df.abs_relative_error_pct,.95)),'max_abs_error_pct':float(df.abs_relative_error_pct.max()),'within_tolerance_fraction':float((df.abs_relative_error_pct<=threshold).mean()),'gate':'pass' if len(df)==24 and (df.abs_relative_error_pct<=threshold).all() else 'fail','evidence_class':'independent_KSCE_2023_source_spectrum_transfer_screen','boundary':'published dimensions and rounded sigma_crd values; nearest-spectrum predicate only; native CUFSM/ABAQUS files and source mode-selection metadata unavailable'}
    (OUT/'r03_ksce2023_spectrum_transfer_summary.json').write_text(json.dumps(s,indent=2),encoding='utf-8')
    df.to_csv(OUT/'r03_ksce2023_spectrum_transfer.csv',index=False)
    return s
if __name__=='__main__': print(json.dumps(summarize(),indent=2))
