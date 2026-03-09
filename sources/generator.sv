module generator(
    input [15:0] t_on, 
    input [15:0] period, 
    input clk,      
    input rst,    
    input gen_en,  
    output periode_complete,  
    output pwm         
    );
    

    logic [15:0] cnt = 16'b0;
    logic signal = 1'b0;
    
    // A pulse flag which confirms the ending of one period
    logic period_complete_s;   
    
    // predicts the completion of one period. 
    // Needed for the gen_en signal. gen_en hast to be generated one cycle earlier.
    logic period_complete_predict = 1'b0;  

    
    always_ff @(posedge clk) begin
        if(rst) begin
            //period_complete_s <= 1'b0;
            cnt <= 16'b0;
            signal <= 1'b0;;
        end
        else begin
            if (cnt >= period-1) begin
                cnt <= 16'b0;
            end 
            else begin
                cnt <= cnt + 1;
            end      
        end
    end
    
    
    always_ff @(posedge clk) begin   
        if (cnt == period-2)
            period_complete_s <= 1'b1;
        else 
            period_complete_s <= 1'b0;
        
        // Predictor eeded for the gen_en signal. 
        if (cnt == period-3)
            period_complete_predict <= 1'b1;
        else 
            period_complete_predict <= 1'b0;  
    end                    
    
    // drive the output signal
    always_ff @(posedge clk) begin
        if(rst) 
            signal <= 1'b0;
            
        else begin       
            if(period_complete_s && gen_en) 
                signal <= 1'b1;
            else if (cnt >= t_on-1)
                signal <= 1'b0;  
        end                           
    end 

    assign pwm = signal;
    assign periode_complete = period_complete_predict;
    
endmodule
