`timescale 1ns / 1ps
module generator(
    input [15:0] t_on, 
    input [15:0] period, 
    input clk,      
    input rst,    
    input gen_en,  
    output periode_complete,  
    output pwm         
    );
    

    
    // A pulse flag which confirms the ending of one period
    
    // predicts the completion of one period. 
    // Needed for the gen_en signal. gen_en hast to be generated one cycle earlier.

            //period_complete_s <= 1'b0;
                    // Predictor eeded for the gen_en signal. 
                          
    
    // drive the output signal
    endmodule
