----------------------------------------------------------------------------------
-- Company: Wizzdev
-- Engineer: Z.Czarnota
--  
-- Project Name: FGPA_data_transfer_demo
-- Module Name: Source generator
--
-- Additional Comments:
-- Handles a number source generators, and adds theirs output to fifo
-- Adds one source output to fifo at one clock cycle so the sampling frequency must not be 
-- greater than number_of_sources * input_clk_frequency .

-- Revision: 06.2019
----------------------------------------------------------------------------------


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

use IEEE.NUMERIC_STD.ALL;

library UNISIM;
use UNISIM.VComponents.all;

entity source_generator is
    Generic (INPUT_CLK_F : natural := 100e6; -- 100MHz
             TARGET_SAMPLING_FREQ : positive := 1e6;
             NUMBER_OF_SOURCES : positive := 28);
    Port ( clk : in STD_LOGIC;
           ce : STD_LOGIC;
           reset : in STD_LOGIC;
           mode : in STD_LOGIC_VECTOR(3 downto 0);
           
           data_fifo_out : out STD_LOGIC_VECTOR(31 downto 0);
           data_fifo_re : in STD_LOGIC;   
           data_fifo_count : out STD_LOGIC_VECTOR(8 downto 0)
);
end source_generator;

architecture Behavioral of source_generator is

constant f_ratio : natural := INPUT_CLK_F / TARGET_SAMPLING_FREQ;

signal sampling_clk : STD_LOGIC := '0';

signal src_data_valid : STD_LOGIC_VECTOR(NUMBER_OF_SOURCES-1 downto 0);

type DATA_OUT is array (NUMBER_OF_SOURCES-1 downto 0) of STD_LOGIC_VECTOR(15 downto 0);
signal src_data_out : DATA_OUT;

signal fifo_din : STD_LOGIC_VECTOR(15 downto 0);
signal fifo_wr_en : STD_LOGIC;
signal fifo_rd_en : STD_LOGIC;
signal fifo_full : STD_LOGIC;
signal fifo_empty : STD_LOGIC;


begin

assert INPUT_CLK_F > (NUMBER_OF_SOURCES * TARGET_SAMPLING_FREQ) report "Target sampling frequency too high for a given number of sources!" severity error;

    GEN_SRCS:
    for I in 0 to NUMBER_OF_SOURCES-1 generate
    
        SRC_0: if (I mod 2) = 0 generate
            sine: entity work.sine_gen
            generic map(SAMPLING_FREQ => TARGET_SAMPLING_FREQ,
                        SINE_FREQ => (I+1)*10)
            port map(clk => sampling_clk,
                    ce => ce,
                    rst => reset,
                    out_valid =>src_data_valid(I),
                    data_out => src_data_out(I));
        end generate;
        
        SRC_1: if (I mod 2) = 1 generate
            saw: entity work.saw_gen
            generic map(INPUT_CLK_F => TARGET_SAMPLING_FREQ,
                        TARGET_F => INPUT_CLK_F,
                        SLOPE_COUNTER_MAX => (I+1)*1024)
            port map(clk => sampling_clk,
                    ce => ce,
                    rst => reset,
                    out_valid =>src_data_valid(I),
                    data_out => src_data_out(I));
        end generate;
    
    end generate;
    
source_fifo : entity work.fifo_16_32
    port map (
        rd_clk => clk,
        wr_clk => clk,
        rst => reset,
        din => fifo_din,
        wr_en => fifo_wr_en,
        rd_en => data_fifo_re,
        dout => data_fifo_out,
        full => fifo_full,
        empty => fifo_empty,
        rd_data_count => data_fifo_count
        
    );
    
process(clk)
 variable clk_counter : natural := 0;
 variable temp_output_valid : STD_LOGIC := '0';
 variable temp_sources_index : natural := 0;
 variable temp_fifo_wr_en : STD_LOGIC := '0';
 
 begin
         
    if rising_edge(clk) then
    
        temp_output_valid := '0'; -- always set to '0' after one clock cycle!  
        temp_fifo_wr_en := '0';
        
        if (reset = '1') then
        
            clk_counter := 0;
            temp_output_valid := '0';
            temp_sources_index := 0;
            
        elsif ce='1' then
                                
            if clk_counter >= f_ratio then
                sampling_clk <= not sampling_clk;   
                clk_counter := 0;  
                temp_output_valid := '1';
            else
                clk_counter := clk_counter + 1;                      
            end if;
            
            if sampling_clk = '0' then
                if temp_sources_index < NUMBER_OF_SOURCES then
                    fifo_din <= src_data_out(temp_sources_index);
                    temp_fifo_wr_en := '1';
                    temp_sources_index := temp_sources_index + 1;
                end if;
             else
                temp_sources_index := 0;
            end if;
              
        end if;
        
    end if;
   
   fifo_wr_en <= temp_fifo_wr_en;                  
    
 end process;



end Behavioral;
