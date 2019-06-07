----------------------------------------------------------------------------------
-- Company: Wizzdev
-- Engineer: Z.Czarnota
--  
-- Project Name: FGPA_data_transfer_demo
-- Module Name: Saw signal generator 
-- 
-- Revision: 06.2019
----------------------------------------------------------------------------------


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

use IEEE.NUMERIC_STD.ALL;

-- Uncomment the following library declaration if instantiating
-- any Xilinx leaf cells in this code.
--library UNISIM;
--use UNISIM.VComponents.all;

entity saw_gen is
    Generic (INPUT_CLK_F : natural := 100e6;
             TARGET_F : natural := 500e3;
             SLOPE_COUNTER_MAX : natural
            );
    Port ( clk : in STD_LOGIC;
           ce : in STD_LOGIC;
           rst : in STD_LOGIC;
           out_valid : out STD_LOGIC;
           data_out : out STD_LOGIC_VECTOR(15 downto 0));
end saw_gen;

architecture Behavioral of saw_gen is

constant u_SLOPE_COUNTER_MAX : unsigned := to_unsigned(SLOPE_COUNTER_MAX, 16);
constant f_ratio : natural := INPUT_CLK_F / TARGET_F;

signal counter : unsigned(15 downto 0) := (others => '0');

begin

process(clk)
 variable clk_counter : natural := 0;
 variable temp_output_valid : STD_LOGIC := '0';
 
 begin

    if rising_edge(clk) then
    
        temp_output_valid := '0'; -- always set to '0' after one clock cycle!                    
        
        if (rst = '1') then
        
            counter <= (others => '0');
            clk_counter := 0;
            temp_output_valid := '0';
            
        elsif ce='1' then
                  
            clk_counter := clk_counter + 1;  
              
            if clk_counter >= f_ratio then
            
                counter <= counter + 1 ; 
                                 
                if counter = u_SLOPE_COUNTER_MAX then
                    counter <= (others => '0');
                end if;  
                        
                clk_counter := 0;                  
            end if;
            
           temp_output_valid := '1';
              
        end if;
        
    end if;
   
    data_out <= std_logic_vector(counter);
    out_valid <= temp_output_valid; 
    
end process;


end Behavioral;
