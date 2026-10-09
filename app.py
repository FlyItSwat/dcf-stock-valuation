"""Streamlit DCF valuation dashboard."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from valuation import wacc, dcf

st.set_page_config(page_title='DCF Stock Valuation',page_icon='💹',layout='wide')
st.title('DCF Stock Valuation Tool')
st.caption('Unlevered free cash flow model • Enterprise to equity bridge • Sensitivity analysis')
st.info('All values must use consistent units, e.g. ₹ crore for FCF, debt and cash; shares in crore. Example inputs are illustrative, not a real company valuation.')
with st.sidebar:
    st.header('Financial inputs')
    initial=st.number_input('Latest annual free cash flow',value=100.0,step=10.0)
    years=st.slider('Forecast years',3,10,5)
    growth=st.slider('Annual FCF growth (%)',-20.0,40.0,10.0,0.5)
    fade=st.checkbox('Fade growth linearly to terminal growth',value=True)
    terminal_growth=st.slider('Terminal growth (%)',-2.0,8.0,3.0,0.5)
    st.subheader('WACC assumptions')
    eq_weight=st.slider('Equity weight (%)',0,100,80)
    ke=st.number_input('Cost of equity (%)',min_value=0.0,value=12.0,step=0.5)
    kd=st.number_input('Cost of debt (%)',min_value=0.0,value=8.0,step=0.5)
    tax=st.slider('Corporate tax rate (%)',0.0,60.0,25.0,1.0)
    st.subheader('Equity bridge')
    debt=st.number_input('Total debt',min_value=0.0,value=200.0,step=10.0)
    cash=st.number_input('Cash and equivalents',min_value=0.0,value=50.0,step=10.0)
    shares=st.number_input('Shares outstanding',min_value=0.000001,value=50.0,step=1.0,format='%.3f')
    market_price=st.number_input('Current share price (optional comparison)',min_value=0.0,value=35.0,step=1.0)
rate=wacc(eq_weight/100,ke,kd,tax)
st.metric('Calculated WACC',f'{rate:.2f}%')
if fade:
    rates=[growth+(terminal_growth-growth)*(i/(years)) for i in range(years)]
else:
    rates=[growth]*years
try:
    result=dcf(initial,rates,rate,terminal_growth,debt,cash,shares)
except ValueError as exc:
    st.error(str(exc))
    st.stop()
a,b,c,d=st.columns(4)
a.metric('Enterprise value',f'{result["enterprise_value"]:,.2f}')
b.metric('Equity value',f'{result["equity_value"]:,.2f}')
c.metric('Intrinsic value / share',f'{result["value_per_share"]:,.2f}')
d.metric('Terminal value share of EV',f'{result["terminal_fraction"]:.1%}')
if market_price>0:
    st.metric('Upside / downside vs. entered market price',f'{(result["value_per_share"]/market_price-1):+.1%}')
forecast=pd.DataFrame({'Year':list(range(1,years+1)),'Growth rate (%)':rates,
                       'Forecast FCF':result['fcf'],'PV of FCF':result['pv_fcf']})
st.subheader('Cash flow forecast')
st.dataframe(forecast,use_container_width=True,hide_index=True)
fig=go.Figure()
fig.add_trace(go.Bar(x=forecast['Year'],y=forecast['Forecast FCF'],name='Forecast FCF'))
fig.add_trace(go.Scatter(x=forecast['Year'],y=forecast['PV of FCF'],name='Present value of FCF'))
fig.update_layout(xaxis_title='Forecast year',yaxis_title='Currency units',title='Forecast and discounted free cash flows')
st.plotly_chart(fig,use_container_width=True)
st.subheader('Sensitivity: WACC vs. terminal growth')
ws=[round(rate+d,2) for d in [-2,-1,0,1,2]]
gs=[round(terminal_growth+d,2) for d in [-1,-0.5,0,0.5,1]]
rows=[]
for g in gs:
    row={'Terminal growth (%)':g}
    for w in ws:
        try:
            row[f'{w:.2f}% WACC']=round(dcf(initial,rates,w,g,debt,cash,shares)['value_per_share'],2)
        except ValueError:
            row[f'{w:.2f}% WACC']=None
    rows.append(row)
sensitivity=pd.DataFrame(rows)
st.dataframe(sensitivity,use_container_width=True,hide_index=True)
st.subheader('Scenario comparison')
scenarios=[]
for name,delta_growth,delta_wacc in [('Bear',-4,1.5),('Base',0,0),('Bull',4,-1.5)]:
    adjusted=[max(-99.0,x+delta_growth) for x in rates]
    try:
        val=dcf(initial,adjusted,rate+delta_wacc,terminal_growth,debt,cash,shares)
        scenarios.append({'Scenario':name,'WACC (%)':rate+delta_wacc,
                          'First-year growth (%)':adjusted[0],
                          'Value per share':val['value_per_share']})
    except ValueError:
        scenarios.append({'Scenario':name,'WACC (%)':rate+delta_wacc,
                          'First-year growth (%)':adjusted[0],
                          'Value per share':None})
st.dataframe(pd.DataFrame(scenarios),use_container_width=True,hide_index=True)
st.download_button('Download forecast CSV',forecast.to_csv(index=False),'dcf_forecast.csv','text/csv')
st.download_button('Download sensitivity CSV',sensitivity.to_csv(index=False),'dcf_sensitivity.csv','text/csv')
st.warning('Educational model, not investment advice. Terminal value can dominate the estimate. Constant WACC, simplified cash flows and growth assumptions may not reflect reality. No market data is downloaded.')
