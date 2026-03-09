   `timescale 1ns / 1ps
module output_controller(
    input [7:0] n,
    input trig,
    input rst,
    input mode,
    input one_period_c,
    input clk,
    output en
    );
    
    logic [7:0] periods_cnt = 8'b0;
    logic en_s = 1'b0;
    logic count_en = 1'b0;
    logic trig_q = 1'b0;
    logic trig_pulse;
    
    // Generate one pulse when the n-mode is triggered via i_trig
    always_ff @(posedge clk) begin
        trig_q <= trig;
    end
    assign trig_pulse = !trig_q && trig;
    
    
    
    always_ff @(posedge clk) begin
        // the counter will be enable here and disabled in the line 63
        if(trig_pulse)
            count_en <= 1'b1;
    end
    
    
    
    always_ff @(posedge clk) begin
        if (rst) begin
            periods_cnt <= 8'b0;
            en_s <= 1'b0;
        end
        else if (one_period_c && count_en && mode==1'b1 ) begin
            if (periods_cnt == n) begin
                periods_cnt <= 8'b0;
                en_s <= 1'b0;
                count_en <= 1'b0;
            end 
            else begin    
                en_s <= 1'b1;
                periods_cnt <= periods_cnt + 1;
            end   
        end  
        
        else if (mode==1'b0)
            en_s <= 1'b1;
    end    
    
    
    assign en = en_s;
    
endmodule

