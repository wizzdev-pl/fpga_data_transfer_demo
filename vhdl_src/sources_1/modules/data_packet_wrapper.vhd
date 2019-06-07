----------------------------------------------------------------------------------
-- Company: Wizzdev
-- Engineer: Z.Czarnota
--  
-- Project Name: FGPA_data_transfer_demo
-- Module Name: Data packet wrapper
--
-- Revision: 06.2019
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

use IEEE.NUMERIC_STD.ALL;


entity data_packet_wrapper is
    Generic (PACKET_LENGTH : positive := 512;
             PACKET_ID_LENGTH : positive := 32;
             CRC_LENGTH : positive := 32);
    Port (  
            clk_in :    in STD_LOGIC;
            reset :     in STD_LOGIC; 
    
            data_fifo_out : in STD_LOGIC_VECTOR(31 downto 0);
            data_fifo_re : out STD_LOGIC;   
            data_fifo_count : in STD_LOGIC_VECTOR(8 downto 0);     
            
       
            packets_fifo_we : out STD_LOGIC;
            packets_fifo_in : out STD_LOGIC_VECTOR(31 downto 0);
            packets_fifo_full : in STD_LOGIC
                                                 
         );
         
end data_packet_wrapper;

architecture arch1 of data_packet_wrapper is

constant BUGFFER_LENGTH : positive := 32;
constant PACKET_LENGTH_TO_CHECKSUM    : positive := (PACKET_LENGTH-CRC_LENGTH)/CRC_LENGTH;
constant BUFFERS_IN_PACKET : positive := PACKET_LENGTH/BUGFFER_LENGTH;

--signal buffers_count : integer range -1 to PACKET_LENGTH/CRC_LENGTH := 0;
--signal packet_ID : unsigned(PACKET_ID_LENGTH-1 downto 0);
--signal checksum : unsigned(CRC_LENGTH-1 downto 0);

type STATE_TYPE is (S0, S1, S2, SERROR, S_wait_for_write, S_write);
signal state : STATE_TYPE := S0;
 
begin

process (clk_in)
variable read_source_next_cycle : STD_LOGIC := '0';
variable read_source_in_2cycles : STD_LOGIC := '0';
variable temp_checksum : unsigned(CRC_LENGTH-1 downto 0) := (others => '0');
variable packet_ID : unsigned(PACKET_ID_LENGTH-1 downto 0) := (others => '0');
variable buffers_count : integer range -1 to PACKET_LENGTH/CRC_LENGTH := 0;
variable output_enable : STD_LOGIC := '0';

variable temp_buffer_out : STD_LOGIC_VECTOR(31 downto 0);

    begin
    if rising_edge(clk_in) then
    
 
        output_enable := '0';
        

        if (reset = '1') then
        
            packet_ID := (others => '0');
            buffers_count := 0;
            state <= S0;
              
        else
               
       case state is 
        when S0 =>
            if (packets_fifo_full /= '1') then
                buffers_count := 0;
                temp_buffer_out := STD_LOGIC_VECTOR(packet_ID);     -- assign packet ID
                temp_checksum := packet_ID;
                packet_ID := packet_ID + 1;
                --if unsigned(data_fifo_count)>2 then
                --    read_source_next_cycle := '1';
                --end if;
                --state <= S1; 
                --buffers_count :=  buffers_count + 1;  
                state <= S_wait_for_write;
               -- output_enable := '1';  
            end if;
      
        when S1 => 
            if (read_source_next_cycle = '1') then
                    temp_buffer_out := data_fifo_out;
                    --buffers_count :=  buffers_count + 1; 
                    temp_checksum := temp_checksum + unsigned(data_fifo_out);

                    read_source_next_cycle := '0';
                    
                    state <= S_wait_for_write; 
            elsif (unsigned(data_fifo_count)>2) then
                    read_source_next_cycle := '1';         
            end if; 
            
        
        when S2 =>
             temp_buffer_out := STD_LOGIC_VECTOR(temp_checksum);
             state <= S_wait_for_write;   
             
        when S_wait_for_write => 
            if (packets_fifo_full /= '1') then
                output_enable := '1';  
                state <= S_write;
            end if;
            
        when S_write =>
            buffers_count :=  buffers_count + 1;  
            if (buffers_count = BUFFERS_IN_PACKET) then
                state <= S0;            
            elsif (buffers_count = PACKET_LENGTH_TO_CHECKSUM) then
                state <= S2;
            else
                if (unsigned(data_fifo_count)>2) then
                    read_source_next_cycle := '1';  
                end if;
                state <=  S1;
            end if;
             
        when SERROR =>
               temp_buffer_out := (others => '1');
               output_enable := '1';
     
        end case; 
        
--        if packets_fifo_full='1' then
--            state <= SERROR;
--        end if;                                                
            
        end if;
    end if;
    
        data_fifo_re <= read_source_next_cycle;
        packets_fifo_in <= temp_buffer_out;
        packets_fifo_we <= output_enable;
        
end process;


end arch1;
