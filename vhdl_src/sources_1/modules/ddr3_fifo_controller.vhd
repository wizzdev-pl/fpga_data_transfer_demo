----------------------------------------------------------------------------------
-- Company: Wizzdev
-- Engineer: Z.Czarnota
--  
-- Project Name: FGPA_data_transfer_demo
-- Module Name: DDR3 fifo controller

-- Revision: 06.2019
----------------------------------------------------------------------------------


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;


use IEEE.NUMERIC_STD.ALL;


library UNISIM;
use UNISIM.VComponents.all;

entity ddr3_fifo_controller is
  Generic (PACKET_LENGTH : positive;
           PACKET_ID_LENGTH : positive;
           CRC_LENGTH : positive);
  Port (
      ui_clk                        : in    std_logic;
      rst                           : in    std_logic; 
      -- DDR3 app interface  
      ddr3_input_buffer             : out   std_logic_vector(255 downto 0);   
      app_addr                      : out    std_logic_vector(28 downto 0);
      app_cmd                       : out    std_logic_vector(2 downto 0);
      app_en                        : out    std_logic;
      app_wdf_end                   : out    std_logic;
      app_wdf_wren                  : out    std_logic;
      app_rd_data_valid             : in   std_logic;
      app_rdy                       : in   std_logic;
      app_wdf_rdy                   : in   std_logic;
      init_calib_complete           : in   std_logic;
      
      -- data in interface
      packets_fifo_out              : in    std_logic_vector(255 downto 0);
      packets_fifo_re               : out   std_logic;
      packets_fifo_count            : in    std_logic_vector(10 downto 0);
      packets_fifo_valid            : in    std_logic;
      -- data out interface
      fifo_pipeout_we               : out   std_logic;
      fifo_pipeout_full             : in    std_logic;
      -- fifo flags
      ddr3_empty                    : inout   std_logic;
      ddr3_full                     : inout   std_logic;
      fifo_out_write_data_count     : in      std_logic_vector(9 downto 0);
      fill_level                    : inout   integer := 0;
      
      DEBUG_OUT                     : out     std_logic_vector(7 downto 0)            
      
    );
end ddr3_fifo_controller;

architecture Behavioral of ddr3_fifo_controller is

attribute keep : string;
attribute keep of ddr3_input_buffer    : signal is "true";
attribute keep of app_addr             : signal is "true";  
attribute keep of app_cmd              : signal is "true";  
attribute keep of app_en               : signal is "true";  
attribute keep of app_wdf_end          : signal is "true";  
attribute keep of app_wdf_wren         : signal is "true";  
attribute keep of app_rd_data_valid    : signal is "true";  
attribute keep of app_rdy              : signal is "true";  
attribute keep of app_wdf_rdy          : signal is "true";  
attribute keep of init_calib_complete  : signal is "true";  
                  

constant BURST_WORD_COUNT : integer := PACKET_LENGTH/256;
constant PACKET_LENGTH_IN_BYTES : integer := PACKET_LENGTH/8;

constant ADDR_INCREMENT : integer := 8;
constant addr_max : natural := (2**28)-ADDR_INCREMENT;       -- max addr in DDR3 - 7 
--signal fill_level : integer := 0; -- in Bytes

constant CMD_READ : STD_LOGIC_VECTOR(2 downto 0) := "001";
constant CMD_WRITE : STD_LOGIC_VECTOR(2 downto 0) := "000";

type STATE_TYPE is (S0, write0, write1, write2, write3, write4, read0, read1, read2, read3);
signal state : STATE_TYPE := S0;

begin


DDR3_fifo:  process(ui_clk)

variable ddr3_addr : std_logic_vector(28 downto 0) := (others => '0');
variable addr_w : natural range 0 to 2**28-1 := 0;   --fifo head
variable addr_r : natural range 0 to 2**28-1 := 0;   --fifo tail
variable ddr3_addr_looped : boolean := false;
variable ddr3_temp_buffer : std_logic_vector(255 downto 0) := (others => '0');
variable write_word_count : integer := 0;
variable read_word_count : integer := 0;


-- procedure that keeps tracks of fifo full/empty fags
procedure UPDATE_FIFO_FLAGS 
    (addr_w : natural;
     addr_r : natural;
     addr_looped : boolean) is
begin
    if addr_r = addr_w then  
        if addr_looped then
            ddr3_full <= '1';
            ddr3_empty <= '0';           
        else
            ddr3_empty <= '1';
            ddr3_full <= '0';
        end if;        
    else
        case addr_looped is
        when true   =>   fill_level <= (addr_w + addr_r)*4;
        when false  =>   fill_level <= (addr_w - addr_r)*4;
        end case;
            
        ddr3_empty <= '0';
        ddr3_full <= '0';
    end if;
end procedure;

begin

    if rising_edge(ui_clk) then
    
        if rst='1' then
            state <= S0;
            write_word_count := 0;
            read_word_count := 0;
            ddr3_addr := (others => '0');
            addr_w := 0;
            addr_r := 0;
            ddr3_addr_looped := false;  
            UPDATE_FIFO_FLAGS(addr_w, addr_r, ddr3_addr_looped);
            
            app_en          <= '0';
            app_wdf_wren    <= '0';
            app_wdf_end     <= '0';
            packets_fifo_re <= '0';
            fifo_pipeout_we <= '0';
           
        else   

        --initially reset all control signals
        app_en          <= '0';
        app_wdf_wren    <= '0';
        app_wdf_end     <= '0';
        packets_fifo_re <= '0';
        fifo_pipeout_we <= '0';
          
        case state is
        
        when S0 =>
            write_word_count := BURST_WORD_COUNT -1;
            read_word_count := BURST_WORD_COUNT -1;
            if (init_calib_complete = '1') then
            
                if ( (fifo_out_write_data_count<std_logic_vector(to_unsigned(1024-2-BURST_WORD_COUNT, 10))) and (fill_level>(2*PACKET_LENGTH_IN_BYTES)) )  then
                    -- reading
                   ddr3_addr := std_logic_vector(to_unsigned(addr_r, 29)); 
                   app_cmd <= CMD_READ; 
                   state <= read0;
              
                elsif (ddr3_full/='1') and (unsigned(packets_fifo_count)>(2*BURST_WORD_COUNT+1)) then
                    --writing
                    ddr3_addr := std_logic_vector(to_unsigned(addr_w, 29));      
                    app_cmd <= CMD_WRITE;
                    state <= write0;
                    
                end if;
            end if;
                                             
        when write0 =>
            --packets_fifo_re <= '1';
            app_en <= '1';
            state <= write1;
        
        when write1 => 
            -- wait for app rdy
            if (app_rdy='1') then
                -- increment address
                if (addr_w >= addr_max) then
                    addr_w := 0;
                    ddr3_addr_looped := true;
                else
                    addr_w := addr_w + ADDR_INCREMENT;
                end if;                
                UPDATE_FIFO_FLAGS(addr_w, addr_r, ddr3_addr_looped);
                state <= write2;
            else
                app_en <= '1';
                
            end if;
        
        when write2 =>
            --wait for app_wdf_rdy
            if (app_wdf_rdy='1') then
                packets_fifo_re <= '1';
                --ddr3_temp_buffer := packets_fifo_out;
                state <= write3;
            end if;
        
        when write3 =>
        -- if fifo out valid
            if (packets_fifo_valid = '1') then
                ddr3_temp_buffer := packets_fifo_out;
                state <= write4;
            end if;
       
        when write4 =>
            app_wdf_wren <= '1';
            app_wdf_end  <= '1';
            if (write_word_count = 0) then   
                --UPDATE_FIFO_FLAGS(addr_w, addr_r, ddr3_addr_looped);
                state <= S0;
            else
                -- wait until RAM write request is completed and controller accepts another commands:
                if (app_wdf_rdy='1') then
                    write_word_count := write_word_count - 1;
                    ddr3_addr := std_logic_vector(to_unsigned(addr_w, 29));  
                    state <= write0;
                end if;
                    
            end if;
            
        
        when read0 =>
            app_en <= '1';
		    state <= read1;
        
        when read1 =>
            if (app_rdy='1') then
                if (addr_r >= addr_max) then
                    addr_r := 0;
                    ddr3_addr_looped := false;
                else
                    addr_r := addr_r + ADDR_INCREMENT;
                end if;
                
                UPDATE_FIFO_FLAGS(addr_w, addr_r, ddr3_addr_looped);
                state <= read2;
            else
                app_en <= '1';
               -- app_cmd <= CMD_READ;
            end if; 
        
        when read2 =>
            -- wait for app_rd_data_valid 
            if (app_rd_data_valid='1') then
--                fifo_pipeout_we <= '1';
                if (read_word_count = 0) then
                    state <= S0;
                else
                    read_word_count := read_word_count - 1;
                    ddr3_addr := std_logic_vector(to_unsigned(addr_r, 29)); 
                    state <= read0;
                end if;
           end if;
--            if (app_rd_data_valid='1') then
--                fifo_pipeout_we <= '1';
--                if (word_count=0) then
--                    state <= S0;
--                else
--                    state <= read1;
--                end if;
--            end if;

        when read3 =>
             if (app_rd_data_valid='1') then
                --UPDATE_FIFO_FLAGS(addr_w, addr_r, ddr3_addr_looped);
                state <= S0;
             end if;
        
        end case;
                  
        end if;
        
     end if;
    
    app_addr <= ddr3_addr;
    ddr3_input_buffer <= ddr3_temp_buffer;

end process;

fifo_pipeout_we <= app_rd_data_valid;

DEBUG_OUT(0) <= '1' when state=S0 else 'Z';
DEBUG_OUT(1) <= '1' when state=write0 else 'Z';
DEBUG_OUT(2) <= '1' when state=write1 else 'Z';
DEBUG_OUT(3) <= '1' when state=write2 else 'Z';
DEBUG_OUT(4) <= '1' when state=write3 else 'Z';
DEBUG_OUT(5) <= '1' when state=write4 else 'Z';
DEBUG_OUT(6) <= '1' when state=read0 else 'Z';
DEBUG_OUT(7) <= '1' when state=read1 else 'Z';





end Behavioral;
