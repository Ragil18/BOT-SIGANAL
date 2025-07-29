import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime

class Backtester:
    """Class for backtesting trading strategies"""
    
    def __init__(self):
        self.commission = 0.001  # 0.1% commission per trade
        self.slippage = 0.0005   # 0.05% slippage
    
    def run_backtest(self, data: pd.DataFrame, signals: pd.DataFrame, 
                     initial_capital: float = 10000) -> Dict[str, Any]:
        """Run a comprehensive backtest"""
        
        if signals.empty or data.empty:
            return self._empty_results(initial_capital)
        
        # Initialize portfolio
        portfolio = {
            'cash': initial_capital,
            'position': 0,  # Number of shares
            'entry_price': 0,
            'total_value': initial_capital
        }
        
        trades = []
        portfolio_history = []
        
        # Process each signal
        for timestamp, signal_row in signals.iterrows():
            if timestamp not in data.index:
                continue
                
            current_price = data.loc[timestamp, 'Close']
            signal_type = signal_row['signal']
            signal_strength = signal_row['strength']
            
            # Apply slippage
            if signal_type == 'BUY':
                execution_price = current_price * (1 + self.slippage)
            elif signal_type == 'SELL':
                execution_price = current_price * (1 - self.slippage)
            else:
                execution_price = current_price
            
            # Execute trades
            if signal_type == 'BUY' and portfolio['position'] == 0:
                # Enter long position
                shares_to_buy = int((portfolio['cash'] * 0.95) / execution_price)  # 95% of cash
                if shares_to_buy > 0:
                    cost = shares_to_buy * execution_price
                    commission_cost = cost * self.commission
                    total_cost = cost + commission_cost
                    
                    if total_cost <= portfolio['cash']:
                        portfolio['cash'] -= total_cost
                        portfolio['position'] = shares_to_buy
                        portfolio['entry_price'] = execution_price
                        
                        trades.append({
                            'timestamp': timestamp,
                            'type': 'BUY',
                            'shares': shares_to_buy,
                            'price': execution_price,
                            'cost': total_cost,
                            'commission': commission_cost,
                            'signal_strength': signal_strength
                        })
            
            elif signal_type == 'SELL' and portfolio['position'] > 0:
                # Exit long position
                shares_to_sell = portfolio['position']
                revenue = shares_to_sell * execution_price
                commission_cost = revenue * self.commission
                net_revenue = revenue - commission_cost
                
                portfolio['cash'] += net_revenue
                portfolio['position'] = 0
                
                # Calculate profit/loss
                entry_cost = shares_to_sell * portfolio['entry_price']
                profit_loss = net_revenue - entry_cost
                profit_loss_pct = (profit_loss / entry_cost) * 100
                
                trades.append({
                    'timestamp': timestamp,
                    'type': 'SELL',
                    'shares': shares_to_sell,
                    'price': execution_price,
                    'revenue': net_revenue,
                    'commission': commission_cost,
                    'profit_loss': profit_loss,
                    'profit_loss_pct': profit_loss_pct,
                    'signal_strength': signal_strength
                })
                
                portfolio['entry_price'] = 0
            
            # Calculate portfolio value
            if portfolio['position'] > 0:
                position_value = portfolio['position'] * current_price
            else:
                position_value = 0
            
            portfolio['total_value'] = portfolio['cash'] + position_value
            
            portfolio_history.append({
                'timestamp': timestamp,
                'cash': portfolio['cash'],
                'position_value': position_value,
                'portfolio_value': portfolio['total_value'],
                'position_shares': portfolio['position']
            })
        
        # Create portfolio history DataFrame
        portfolio_df = pd.DataFrame(portfolio_history)
        if not portfolio_df.empty:
            portfolio_df.set_index('timestamp', inplace=True)
        
        # Calculate performance metrics
        results = self._calculate_performance_metrics(
            portfolio_df, trades, initial_capital, data
        )
        
        results['portfolio_history'] = portfolio_df
        results['trades'] = trades
        
        return results
    
    def _calculate_performance_metrics(self, portfolio_history: pd.DataFrame, 
                                     trades: List[Dict], initial_capital: float,
                                     price_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        
        if portfolio_history.empty:
            return self._empty_results(initial_capital)
        
        final_value = portfolio_history['portfolio_value'].iloc[-1]
        total_return = ((final_value - initial_capital) / initial_capital) * 100
        
        # Trade statistics
        profitable_trades = [t for t in trades if t.get('profit_loss', 0) > 0]
        losing_trades = [t for t in trades if t.get('profit_loss', 0) < 0]
        
        total_trades = len([t for t in trades if t['type'] == 'SELL'])
        win_rate = (len(profitable_trades) / total_trades * 100) if total_trades > 0 else 0
        
        # Profit/Loss statistics
        if profitable_trades:
            avg_win = np.mean([t['profit_loss'] for t in profitable_trades])
            max_win = max([t['profit_loss'] for t in profitable_trades])
        else:
            avg_win = 0
            max_win = 0
        
        if losing_trades:
            avg_loss = np.mean([t['profit_loss'] for t in losing_trades])
            max_loss = min([t['profit_loss'] for t in losing_trades])
        else:
            avg_loss = 0
            max_loss = 0
        
        # Risk metrics
        returns = portfolio_history['portfolio_value'].pct_change().dropna()
        
        # Maximum drawdown
        peak = portfolio_history['portfolio_value'].expanding().max()
        drawdown = (portfolio_history['portfolio_value'] - peak) / peak * 100
        max_drawdown = drawdown.min()
        
        # Sharpe ratio (assuming risk-free rate of 2%)
        risk_free_rate = 0.02
        if returns.std() != 0:
            excess_returns = returns.mean() * 252 - risk_free_rate  # Annualized
            sharpe_ratio = excess_returns / (returns.std() * np.sqrt(252))
        else:
            sharpe_ratio = 0
        
        # Sortino ratio
        negative_returns = returns[returns < 0]
        if len(negative_returns) > 0 and negative_returns.std() != 0:
            sortino_ratio = excess_returns / (negative_returns.std() * np.sqrt(252))
        else:
            sortino_ratio = 0
        
        # Calmar ratio
        if max_drawdown != 0:
            calmar_ratio = (total_return / 100) / abs(max_drawdown / 100)
        else:
            calmar_ratio = 0
        
        # Buy and hold comparison
        if not price_data.empty:
            buy_hold_return = ((price_data['Close'].iloc[-1] - price_data['Close'].iloc[0]) / 
                             price_data['Close'].iloc[0]) * 100
        else:
            buy_hold_return = 0
        
        return {
            'initial_capital': initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profitable_trades': len(profitable_trades),
            'losing_trades': len(losing_trades),
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_win': max_win,
            'max_loss': max_loss,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'buy_hold_return': buy_hold_return,
            'alpha': total_return - buy_hold_return,
            'total_commission': sum([t.get('commission', 0) for t in trades]),
            'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else 0
        }
    
    def _empty_results(self, initial_capital: float) -> Dict[str, Any]:
        """Return empty results when no trades are made"""
        return {
            'initial_capital': initial_capital,
            'final_value': initial_capital,
            'total_return': 0.0,
            'total_trades': 0,
            'win_rate': 0.0,
            'profitable_trades': 0,
            'losing_trades': 0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'max_win': 0.0,
            'max_loss': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'calmar_ratio': 0.0,
            'buy_hold_return': 0.0,
            'alpha': 0.0,
            'total_commission': 0.0,
            'profit_factor': 0.0,
            'portfolio_history': pd.DataFrame(),
            'trades': []
        }
    
    def calculate_var(self, returns: pd.Series, confidence_level: float = 0.05) -> float:
        """Calculate Value at Risk"""
        if returns.empty:
            return 0
        return np.percentile(returns, confidence_level * 100)
    
    def calculate_expected_shortfall(self, returns: pd.Series, confidence_level: float = 0.05) -> float:
        """Calculate Expected Shortfall (Conditional VaR)"""
        if returns.empty:
            return 0
        var = self.calculate_var(returns, confidence_level)
        return returns[returns <= var].mean()
    
    def monte_carlo_simulation(self, data: pd.DataFrame, signals: pd.DataFrame, 
                             initial_capital: float, num_simulations: int = 1000) -> Dict[str, Any]:
        """Run Monte Carlo simulation for strategy robustness testing"""
        results = []
        
        for _ in range(num_simulations):
            # Add random noise to prices
            noise_factor = np.random.normal(1, 0.02, len(data))
            noisy_data = data.copy()
            noisy_data[['Open', 'High', 'Low', 'Close']] *= noise_factor.reshape(-1, 1)
            
            # Run backtest with noisy data
            result = self.run_backtest(noisy_data, signals, initial_capital)
            results.append(result['total_return'])
        
        return {
            'mean_return': np.mean(results),
            'std_return': np.std(results),
            'min_return': np.min(results),
            'max_return': np.max(results),
            'percentile_5': np.percentile(results, 5),
            'percentile_95': np.percentile(results, 95),
            'probability_positive': len([r for r in results if r > 0]) / len(results) * 100
        }
