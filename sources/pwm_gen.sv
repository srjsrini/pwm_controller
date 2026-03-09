`timescale 1ns / 1ps
module pwm_module(
    input [15:0] i_duty,        // duty cycle
    input [15:0] i_limit,       // period
    input [7:0 ]i_n,            // number of cycles for the n-cycle mode
    input i_trig,               // triggers the n-cylce generation
    input i_mode,         // 0 = continous PWM,  1 = n-cycles mode
    input i_clk,                // system clock
    input i_rst,                // reset, active high
    output o_pwm                // output signal
    );
    

    logic gen_en_s;        
    logic periode_complete_s;      

	//Instantiate generator module
	//Instantiate output_controller module  
    
endmodule

