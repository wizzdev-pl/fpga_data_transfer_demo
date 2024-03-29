----------------------------------------------------------------------------------
-- Company: Wizzdev
-- Engineer: Z.Czarnota
--  
-- Project Name: FGPA_data_transfer_demo
-- Module Name: Sine signal generator using lookup table and phase accumulaor
-- 
-- Revision: 06.2019
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

use IEEE.NUMERIC_STD.ALL;

use ieee.math_real.all;

library UNISIM;
use UNISIM.VComponents.all;

entity sine_gen is
    Generic (SAMPLING_FREQ : positive := 100e6;
             SINE_FREQ : positive := 1e3  
             );
    Port ( clk : in STD_LOGIC;
            ce : in STD_LOGIC;
            rst : in STD_LOGIC;
           out_valid : out STD_LOGIC;
           data_out : out STD_LOGIC_VECTOR(15 downto 0)
           );
end sine_gen;

architecture Behavioral of sine_gen is

    constant NUMBER_OF_SAMPLES : positive := 2**8;
    constant ACCU_WIDTH : positive := 30;
    constant FREQ_RATIO : positive := SAMPLING_FREQ / SINE_FREQ;
    constant PHASE_INCREMENT : positive := (2**ACCU_WIDTH) / FREQ_RATIO;
    
    type t_sin_table is array(0 to NUMBER_OF_SAMPLES-1) of integer range 0 to 2**16-1;
    
    constant SIN_LOOKUP_TABLE : t_sin_table := (
        32768,	33572,	34375,	35178,	35979,	36779,	37576,	38370,	39160,	39947,	40729,	41507,	42280,	43046,	43807,	44561,
        45307,	46046,	46778,	47500,	48214,	48919,	49614,	50298,	50972,	51636,	52287,	52927,	53555,	54171,	54773,	55362,
        55938,	56500,	57047,	57580,	58098,	58600,	59087,	59558,	60013,	60452,	60874,	61279,	61666,	62037,	62389,	62724,
        63041,	63340,	63620,	63882,	64125,	64349,	64553,	64739,	64906,	65053,	65181,	65289,	65378,	65447,	65496,	65526,
        65535,	65526,	65496,	65447,	65378,	65289,	65181,	65053,	64906,	64739,	64553,	64349,	64125,	63882,	63620,	63340,
        63041,	62724,	62389,	62037,	61666,	61279,	60874,	60452,	60013,	59558,	59087,	58600,	58098,	57580,	57047,	56500,
        55938,	55362,	54773,	54171,	53555,	52927,	52287,	51636,	50972,	50298,	49614,	48919,	48214,	47500,	46778,	46046,
        45307,	44561,	43807,	43046,	42280,	41507,	40729,	39947,	39160,	38370,	37576,	36779,	35979,	35178,	34375,	33572,
        32768,	31963,	31160,	30357,	29556,	28756,	27959,	27165,	26375,	25588,	24806,	24028,	23255,	22489,	21728,	20974,
        20228,	19489,	18757,	18035,	17321,	16616,	15921,	15237,	14563,	13899,	13248,	12608,	11980,	11364,	10762,	10173,
        9597,	9035,	8488,	7955,	7437,	6935,	6448,	5977,	5522,	5083,	4661,	4256,	3869,	3498,	3146,	2811,
        2494,	2195,	1915,	1653,	1410,	1186,	982,	796,	629,	482,	354,	246,	157,	88,	39,	9,
        0,	9,	39,	88,	157,	246,	354,	482,	629,	796,	982,	1186,	1410,	1653,	1915,	2195,
        2494,	2811,	3146,	3498,	3869,	4256,	4661,	5083,	5522,	5977,	6448,	6935,	7437,	7955,	8488,	9035,
        9597,	10173,	10762,	11364,	11980,	12608,	13248,	13899,	14563,	15237,	15921,	16616,	17321,	18035,	18757,	19489,
        20228,	20974,	21728,	22489,	23255,	24028,	24806,	25588,	26375,	27165,	27959,	28756,	29556,	30357,	31160,	31963
        );
        
signal phase_accumulator : unsigned(ACCU_WIDTH-1 downto 0) := (others => '0');
    
begin

process(clk)
variable current_phase : unsigned(7 downto 0);
variable temp_output_valid : STD_LOGIC := '0';

variable temp_index : natural;
variable temp_index_counter : natural := 0;
variable temp_sin : integer;

begin
    if rising_edge(clk) then
    
        temp_output_valid := '0';       -- set to zero after every full clock cicle
    
        if (rst = '1') then
            phase_accumulator <= (others => '0');
            
        elsif (ce = '1') then
            
            current_phase := phase_accumulator(ACCU_WIDTH-1 downto ACCU_WIDTH-8);
            temp_sin := SIN_LOOKUP_TABLE(to_integer(current_phase));
            data_out <= std_logic_vector(to_unsigned(temp_sin, 16));
            
            phase_accumulator <= phase_accumulator + PHASE_INCREMENT;
                            
            temp_output_valid := '1';
        end if;
  
    end if;

    out_valid <= temp_output_valid;
end process;

end Behavioral;
