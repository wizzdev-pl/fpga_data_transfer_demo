----------------------------------------------------------------------------------
-- Company: Wizzdev
-- Engineer: Z.Czarnota
--  
-- Project Name: FGPA_data_transfer_demo
-- Module Name: demo_top.vhd

-- Additional Comments: 
-- Top module for the FGPA_data_transfer_demo project

-- Revision: 06.2019
----------------------------------------------------------------------------------


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

use IEEE.NUMERIC_STD.ALL;

library UNISIM;
use UNISIM.VComponents.all;

use work.FRONTPANEL.all;


entity new_demo_top is
    Generic (NUMBER_OF_SRCS : positive := 4;
            SAMPLING_FREQUENCY : positive := 1e3;
            PACKET_LENGTH : positive := 4096;
            PACKET_ID_LENGTH : positive := 32;
            CRC_LENGTH : positive := 32);
    Port ( 
           -- USB3.0 interface
           okUH     : in STD_LOGIC_VECTOR(4 downto 0);
           okHU     : out STD_LOGIC_VECTOR(2 downto 0);
           okUHU    : inout STD_LOGIC_VECTOR(31 downto 0);
           okAA     : inout STD_LOGIC;
           
           -- onboard clock
           sys_clkp : in STD_LOGIC;
           sys_clkn : in STD_LOGIC;
           
           -- DDR3 interface
           ddr3_dq      : inout STD_LOGIC_VECTOR(31 downto 0);
           ddr3_dqs_p   : inout std_logic_vector(3 downto 0);
           ddr3_dqs_n   : inout std_logic_vector(3 downto 0);
           
           ddr3_addr    : out STD_LOGIC_VECTOR(14 downto 0);
           ddr3_ba      : out STD_LOGIC_VECTOR(2 downto 0);
           ddr3_ck_p    : out STD_LOGIC_VECTOR(0 downto 0);
           ddr3_ck_n    : out STD_LOGIC_VECTOR(0 downto 0);
           ddr3_cke     : out STD_LOGIC_VECTOR(0 downto 0);
           ddr3_dm      : out   STD_LOGIC_VECTOR(3 downto 0);
           ddr3_odt     : out   STD_LOGIC_VECTOR(0 downto 0);
           ddr3_ras_n   : out   std_logic;
           ddr3_cas_n   : out   std_logic;
           ddr3_we_n    : out   std_logic;
           ddr3_reset_n : out   std_logic;
          
           -- onboard LEDs       
           debug_LEDs : out STD_LOGIC_VECTOR(7 downto 0) := (others => 'Z'));
end new_demo_top;

architecture Behavioral of new_demo_top is

constant USABLE_PACKET_LENGTH : natural := PACKET_LENGTH - (PACKET_ID_LENGTH + CRC_LENGTH);
constant USB_BUFFER_LENGTH : natural := 8*1024; -- in Bytes, the BLOCK_LENGTH for BlockThrottledPipe transfers

signal ui_clk : STD_LOGIC;      -- 100Mhz generated from MIG
signal clk_200MHz : STD_LOGIC;
signal mig_clk : STD_LOGIC; -- 200MHz that goes to mig clk input

-- reset signals
signal ui_rst : STD_LOGIC;
signal sys_rst : STD_LOGIC;
signal rst : STD_LOGIC;
signal general_rst : STD_LOGIC;

-- OpalKelly interfaces 
signal okClk : STD_LOGIC;
signal okHE : STD_LOGIC_VECTOR(112 downto 0);
signal okEH : STD_LOGIC_VECTOR(64 downto 0);
signal okEHx : STD_LOGIC_VECTOR(2*65-1 downto 0);

signal control_out_data : STD_LOGIC_VECTOR(31 downto 0);    -- wireOut data
signal ep00wire : STD_LOGIC_VECTOR(31 downto 0);            -- wireIn data
signal ack_trigg : STD_LOGIC_VECTOR(31 downto 0);            -- triggerIn 


-- okBlockThrottle pipeOut signals
signal pipe_out_read : STD_LOGIC;
signal pipe_out_data : STD_LOGIC_VECTOR(31 downto 0) := (others => '0');
signal pipe_ready : STD_LOGIC;
signal block_strobe : STD_LOGIC;


-- source generator signals
signal src_gen_enable : STD_LOGIC := '0';
signal mode : STD_LOGIC_VECTOR(3 downto 0);
signal source_data_valid : STD_LOGIC;

-- ddr3 interface
signal  app_addr          : std_logic_vector(28 downto 0);  -- DDR3 r/w address
signal  app_cmd           : std_logic_vector(2 downto 0);   -- 000: write 0001: read
signal  app_en            : std_logic := '0';                      
signal  app_wdf_end       : std_logic;
signal  app_wdf_mask      : std_logic_vector(31 downto 0) := (others => '0');
signal  app_wdf_wren      : std_logic;
signal  app_wdf_data       : STD_LOGIC_VECTOR(255 downto 0);
signal  app_rd_data       : std_logic_vector(255 downto 0);
signal  app_rd_data_end   : std_logic;
signal  app_rd_data_valid : std_logic;
signal  app_rdy           :  std_logic;
signal  app_wdf_rdy       :  std_logic;

signal ddr3_calib_done : STD_LOGIC;
signal ddr3_empty      : STD_LOGIC;
signal ddr3_full       : STD_LOGIC;

constant reset_10_ms : natural := 10e6; -- with clock 100MHz
signal ddr_rst_count : natural := 0;

signal ddr3_fill_level : integer;

-- pipeout fifo signals
signal fifo_pipeout_full : STD_LOGIC;
signal fifo_pipeout_empty : STD_LOGIC;
signal fifo_out_almost_empty : STD_LOGIC;
signal fifo_pipeout_we : STD_LOGIC;
signal fifo_out_data : STD_LOGIC_VECTOR(31 downto 0);
signal fifo_out_read_data_count : STD_LOGIC_VECTOR(12 downto 0);
signal fifo_out_write_data_count : STD_LOGIC_VECTOR(9 downto 0);


-- packets fifo
signal packets_fifo_out : STD_LOGIC_VECTOR(255 downto 0);
signal packets_fifo_we : STD_LOGIC;
signal packets_fifo_in : STD_LOGIC_VECTOR(31 downto 0);
signal packets_fifo_re : STD_LOGIC;
signal packets_fifo_ready : STD_LOGIC;
signal packets_fifo_full : STD_LOGIC;
signal packets_fifo_empty : STD_LOGIC;
signal packets_fifo_count : STD_LOGIC_VECTOR(10 downto 0);
signal packets_fifo_valid : STD_LOGIC;

-- source fifo signals
signal source_fifo_rdy : STD_LOGIC;
signal source_fifo_full : STD_LOGIC;
signal source_fifo_half_full : STD_LOGIC;
signal source_fifo_empty : STD_LOGIC;
signal source_fifo_re : STD_LOGIC;
signal source_temp_buff : STD_LOGIC_VECTOR(31 downto 0);
signal source_fifo_din : STD_LOGIC_VECTOR(31 downto 0);
signal source_fifo_we : STD_LOGIC := '0';
signal source_fifo_out : STD_LOGIC_VECTOR(31 downto 0);
signal source_fifo_buff_ready : STD_LOGIC;
signal source_fifo_data_count : STD_LOGIC_VECTOR(8 downto 0);


-- DEBUG
signal debug_info1 : STD_LOGIC_VECTOR(7 downto 0);
signal debug_info2 : STD_LOGIC_VECTOR(7 downto 0);


begin

-- Asserts to check the settings
-- Does usable packet length is a multiply of 16bits ()
assert (USABLE_PACKET_LENGTH mod 16 = 0) report "Incorrect packet length!" severity error;
assert (((USABLE_PACKET_LENGTH/16) mod NUMBER_OF_SRCS) = 0) report "Incorrect packet length for given number of sources!" severity error;

debug_info2(0) <= '1' when packets_fifo_ready = '1' else 'Z';
debug_info2(1) <= '1' when packets_fifo_re = '1' else 'Z';
debug_info2(2) <= '1' when ddr3_empty = '1' else 'Z';
debug_info2(3) <= '1' when ddr3_full = '1' else 'Z';
debug_info2(4) <= '1' when fifo_out_almost_empty = '1' else 'Z';
debug_info2(5) <= '1' when fifo_pipeout_we = '1' else 'Z';
debug_info2(6) <= '1' when fifo_pipeout_full = '1' else 'Z';
debug_info2(7) <= '1' when pipe_ready = '1' else 'Z';

rst <= ep00wire(0);
general_rst <= rst or ui_rst;

mode <= ep00wire(4 downto 1);

control_out_data <= std_logic_vector(to_unsigned(ddr3_fill_level, 32));


debug_LEDs <= debug_info2;

osc_clk : IBUFGDS port map (O=>clk_200MHz, I=>sys_clkp, IB=>sys_clkn);
mig_input_clk : IBUFG port map (O=>mig_clk, I=>clk_200MHz);

check_triggers: process(ui_clk)
begin

    if rising_edge(ui_clk) then
        -- check triggers
       if ack_trigg(0) = '1' then
           src_gen_enable <= '1';
       elsif ack_trigg(1) = '1' then
           src_gen_enable <= '0';
       end if;
       
    end if;
    
end process; 

-- 10ms initial reset
ddr3_reset: process(ui_clk)
begin
    if (ddr_rst_count < reset_10_ms) then
        ddr_rst_count <= ddr_rst_count + 1;
        sys_rst <= '1';
    else
        sys_rst <= '0';      
    end if;
    
end process;

-- for the sanity of bytes order
pipe_out_data(15 downto 0) <= fifo_out_data(31 downto 16);
pipe_out_data(31 downto 16) <= fifo_out_data(15 downto 0);

pipe_ready <= '1' when (fifo_out_read_data_count >= std_logic_vector(to_unsigned(USB_BUFFER_LENGTH/4, 13))) else '0';   -- enable pipe output when full buffer ready to read!!


source_gen0 : entity work.source_generator
    GENERIC MAP (TARGET_SAMPLING_FREQ => SAMPLING_FREQUENCY,
                NUMBER_OF_SOURCES => NUMBER_OF_SRCS)
    PORT MAP(
    clk => ui_clk,
    ce => src_gen_enable,
    reset => general_rst,
    mode => "0000",
    data_fifo_out => source_fifo_out,
    data_fifo_re => source_fifo_re,
    data_fifo_count => source_fifo_data_count
    );


packages_assembler : entity work.data_packet_wrapper
      Generic map (PACKET_LENGTH    => PACKET_LENGTH,
                PACKET_ID_LENGTH    => PACKET_ID_LENGTH,
                CRC_LENGTH          => CRC_LENGTH)
    Port map (  
            clk_in          => ui_clk,
            reset           => general_rst,
  
            data_fifo_out   => source_fifo_out,
            data_fifo_re    => source_fifo_re,
            data_fifo_count => source_fifo_data_count,         
      
            packets_fifo_we => packets_fifo_we,
            packets_fifo_in  => packets_fifo_in,
            packets_fifo_full => packets_fifo_full                   
         );


controller :  entity work.ddr3_fifo_controller
      Generic map (PACKET_LENGTH    => PACKET_LENGTH,
                PACKET_ID_LENGTH    => PACKET_ID_LENGTH,
                CRC_LENGTH          => CRC_LENGTH)
      Port map (
      ui_clk                    => ui_clk,
      rst                       => general_rst,
      -- DDR3 app interface
      ddr3_input_buffer         => app_wdf_data,     
      app_addr                  => app_addr,
      app_cmd                   => app_cmd,
      app_en                    => app_en,
      app_wdf_end               => app_wdf_end,
      app_wdf_wren              => app_wdf_wren,
      app_rd_data_valid         => app_rd_data_valid,
      app_rdy                   => app_rdy,
      app_wdf_rdy               => app_wdf_rdy,
      init_calib_complete       => ddr3_calib_done,
      
      -- data in/out interface  
      packets_fifo_out           => packets_fifo_out,
      packets_fifo_re            => packets_fifo_re,
      packets_fifo_count         => packets_fifo_count,
      packets_fifo_valid        => packets_fifo_valid,
      fifo_pipeout_we           => fifo_pipeout_we,
      fifo_pipeout_full         => fifo_pipeout_full,
      ddr3_empty                => ddr3_empty,
      ddr3_full                 => ddr3_full,
      fifo_out_write_data_count => fifo_out_write_data_count, -- asserted when less than 1024bytes in FIFO
      fill_level                => ddr3_fill_level,
      DEBUG_OUT                 => debug_info1
    ); 
    
mig_inst : entity work.mig_7series_1
    port map (
       -- Memory interface ports
       ddr3_addr                      => ddr3_addr,
       ddr3_ba                        => ddr3_ba,
       ddr3_cas_n                     => ddr3_cas_n,
       ddr3_ck_n                      => ddr3_ck_n,
       ddr3_ck_p                      => ddr3_ck_p,
       ddr3_cke                       => ddr3_cke,
       ddr3_ras_n                     => ddr3_ras_n,
       ddr3_reset_n                   => ddr3_reset_n,
       ddr3_we_n                      => ddr3_we_n,
       ddr3_dq                        => ddr3_dq,
       ddr3_dqs_n                     => ddr3_dqs_n,
       ddr3_dqs_p                     => ddr3_dqs_p,
       init_calib_complete            => ddr3_calib_done,
       ddr3_dm                        => ddr3_dm,
       ddr3_odt                       => ddr3_odt,
       -- Application interface ports
       app_addr                       => app_addr,
       app_cmd                        => app_cmd,
       app_en                         => app_en,
       app_wdf_data                   => app_wdf_data,
       app_wdf_end                    => '1',
       app_wdf_wren                   => app_wdf_wren,
       app_rd_data                    => app_rd_data,
       app_rd_data_end                => app_rd_data_end,
       app_rd_data_valid              => app_rd_data_valid,
       app_rdy                        => app_rdy,
       app_wdf_rdy                    => app_wdf_rdy,
       app_sr_req                     => '0',
       app_ref_req                    => '0',
       app_zq_req                     => '0',
       app_sr_active                  => open,
       app_ref_ack                    => open,
       app_zq_ack                     => open,
       ui_clk                         => ui_clk,
       ui_clk_sync_rst                => ui_rst,
       app_wdf_mask                   => app_wdf_mask,
       -- System Clock Ports
       sys_clk_i                      => mig_clk, -- buff sys_clkp
       sys_rst                        => sys_rst
    );
    
           
    
packets_fifo : entity work.fifo_32_256
  PORT MAP (
    clk => ui_clk,
    srst => general_rst,
    din => packets_fifo_in,
    wr_en => packets_fifo_we,
    rd_en => packets_fifo_re,
    dout => packets_fifo_out,
    full => packets_fifo_full,
    empty => packets_fifo_empty,
    valid => packets_fifo_valid,
    rd_data_count => packets_fifo_count
  );
  
    
fifo_pipeout : entity work.fifo_pipeout
  PORT MAP (
    rst => general_rst,
    wr_clk => ui_clk,
    rd_clk => okClk,
    din => app_rd_data,
    wr_en => fifo_pipeout_we,
    rd_en => pipe_out_read,
    dout => fifo_out_data,
    full => fifo_pipeout_full,
    empty => fifo_pipeout_empty,
    prog_empty => fifo_out_almost_empty,
    rd_data_count => fifo_out_read_data_count,
    wr_data_count => fifo_out_write_data_count,
    wr_rst_busy => open,
    rd_rst_busy => open
  );

-- Instantiate the okHost and connect endpoints
okHI : okHost port map (
	okUH=>okUH, 
	okHU=>okHU, 
	okUHU=>okUHU, 
	okAA=>okAA,
	okClk=>okClk, 
	okHE=>okHE, 
	okEH=>okEH
);

WireOR: okWireOR
    generic map (N => 2)
    port map (okEH   => okEH,
		      okEHx  => okEHx);
		      
ep21 : okWireOut
    port map (okHE => okHE,
              okEH => okEHx(1*65-1 downto 0*65),
              ep_addr => x"21",
              ep_datain => control_out_data);		      

ep40 : okTriggerIn
    port map (okHE          => okHE,
              ep_addr       => x"40",
              ep_clk        => ui_clk,
              ep_trigger    => ack_trigg
              );
              

ep00 : okWireIn     
    port map (okHE          =>  okHE,
              ep_addr       =>  x"00", 
              ep_dataout    =>  ep00wire);


epA0 : okBTPipeOut 
    port map (okHE              =>  okHE,
              okEH              =>  okEHx(2*65-1 downto 1*65),  
              ep_addr           =>  x"A0", 
              ep_read           =>  pipe_out_read, 
              ep_datain         =>  pipe_out_data,
              ep_blockstrobe    =>  block_strobe,
              ep_ready          =>  pipe_ready);


end Behavioral;



