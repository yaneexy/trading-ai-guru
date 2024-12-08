import pyautogui
import time
import logging
from typing import Tuple, Optional

class TradingController:
    def __init__(self):
        # Set PyAutoGUI settings
        pyautogui.PAUSE = 0.5  # Add delay between actions
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort
        
        # Initialize trading positions (to be configured by user)
        self.buy_button_pos: Optional[Tuple[int, int]] = None
        self.sell_button_pos: Optional[Tuple[int, int]] = None
        
    def calibrate_positions(self):
        """Calibrate the position of trading buttons"""
        logging.info("Starting position calibration...")
        print("Move your mouse to the Buy button position and press Enter")
        input()
        self.buy_button_pos = pyautogui.position()
        
        print("Move your mouse to the Sell button position and press Enter")
        input()
        self.sell_button_pos = pyautogui.position()
        
        logging.info(f"Calibration complete. Buy pos: {self.buy_button_pos}, Sell pos: {self.sell_button_pos}")
    
    def execute_buy(self):
        """Execute a buy order"""
        if not self.buy_button_pos:
            raise ValueError("Buy button position not calibrated")
        
        try:
            # Save current mouse position
            original_pos = pyautogui.position()
            
            # Execute buy
            pyautogui.moveTo(self.buy_button_pos)
            pyautogui.click()
            logging.info("Buy order executed")
            
            # Return to original position
            pyautogui.moveTo(original_pos)
            
        except Exception as e:
            logging.error(f"Error executing buy order: {str(e)}")
            raise
    
    def execute_sell(self):
        """Execute a sell order"""
        if not self.sell_button_pos:
            raise ValueError("Sell button position not calibrated")
        
        try:
            # Save current mouse position
            original_pos = pyautogui.position()
            
            # Execute sell
            pyautogui.moveTo(self.sell_button_pos)
            pyautogui.click()
            logging.info("Sell order executed")
            
            # Return to original position
            pyautogui.moveTo(original_pos)
            
        except Exception as e:
            logging.error(f"Error executing sell order: {str(e)}")
            raise

    def verify_position(self, position: Tuple[int, int]) -> bool:
        """Verify if a screen position is valid"""
        screen_width, screen_height = pyautogui.size()
        x, y = position
        return 0 <= x < screen_width and 0 <= y < screen_height
