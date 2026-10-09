"""Transparent, deterministic unlevered DCF calculations (currency units consistent)."""
import math


def wacc(equity_weight, cost_equity_pct, cost_debt_pct, tax_pct):
    """Equity weight 0..1; all other inputs in percent."""
    if not 0 <= equity_weight <= 1 or not 0 <= tax_pct <= 100:
        raise ValueError('Invalid equity weight or tax rate')
    if cost_equity_pct < 0 or cost_debt_pct < 0:
        raise ValueError('Costs of capital cannot be negative')
    return equity_weight * cost_equity_pct + (1-equity_weight)*cost_debt_pct*(1-tax_pct/100)


def forecast_fcf(initial_fcf, growth_rates_pct):
    if not math.isfinite(initial_fcf):
        raise ValueError('Initial FCF must be finite')
    if not growth_rates_pct or len(growth_rates_pct)>30:
        raise ValueError('Provide 1 to 30 forecast years')
    out=[]
    fcf=float(initial_fcf)
    for rate in growth_rates_pct:
        if not math.isfinite(rate) or rate <= -100:
            raise ValueError('Growth rates must be finite and greater than -100%')
        fcf *= (1+rate/100)
        out.append(fcf)
    return out


def dcf(initial_fcf, growth_rates_pct, discount_pct, terminal_growth_pct, debt, cash, shares):
    values=[initial_fcf,discount_pct,terminal_growth_pct,debt,cash,shares]
    if not all(math.isfinite(float(v)) for v in values):
        raise ValueError('Inputs must be finite')
    if shares <= 0 or debt < 0 or cash < 0:
        raise ValueError('Shares must be positive; debt and cash non-negative')
    if discount_pct <= terminal_growth_pct or discount_pct <= -100 or terminal_growth_pct <= -100:
        raise ValueError('Discount rate must exceed terminal growth rate')
    forecasts=forecast_fcf(initial_fcf,growth_rates_pct)
    r=discount_pct/100
    g=terminal_growth_pct/100
    discounted=[v/(1+r)**(i+1) for i,v in enumerate(forecasts)]
    terminal=forecasts[-1]*(1+g)/(r-g)
    terminal_pv=terminal/(1+r)**len(forecasts)
    enterprise=sum(discounted)+terminal_pv
    equity=enterprise-debt+cash
    return {'fcf':forecasts,'pv_fcf':discounted,'terminal_value':terminal,
            'pv_terminal':terminal_pv,'enterprise_value':enterprise,
            'equity_value':equity,'value_per_share':equity/shares,
            'terminal_fraction':terminal_pv/enterprise if enterprise else float('nan')}
