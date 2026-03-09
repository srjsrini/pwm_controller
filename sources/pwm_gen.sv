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


    
    generator one_period_gen(
                            .t_on  (i_duty ),
                            .period(i_limit),
                            .clk   (i_clk  ),    
                            .rst   (i_rst  ),    
                            .gen_en(gen_en_s ),
                            .periode_complete(periode_complete_s),
                            .pwm   (o_pwm   )     );
    
    output_controller output_controller_i(   
                                            .n            (i_n          ),
                                            .trig         (i_trig       ),  
                                            .rst          (i_rst        ),  
                                            .mode         (i_mode       ),
                                            .one_period_c (periode_complete_s),  
                                            .clk          (i_clk        ), 
                                            .en           (gen_en_s       )     );
                                                
    
    
endmodule

