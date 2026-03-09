import cocotb
import os
from pathlib import Path
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from cocotb_tools.runner import get_runner

# ==============================================================================
# ✅ Cocotb Test: Advanced PWM Validation
# ==============================================================================
@cocotb.test()
async def test_pwm_advanced_complete(dut):
    """
    Validates Continuous and N-Cycle modes with period and duty cycle checking.
    """
    
    # Start 100MHz Clock (10ns period)
    cocotb.start_soon(Clock(dut.i_clk, 10, units="ns").start())

    # Initial Reset Phase
    dut.i_rst.value = 1
    dut.i_trig.value = 0
    dut.i_mode.value = 0  # Continuous Mode
    dut.i_duty.value = 0
    dut.i_limit.value = 0x7FFF
    await Timer(30, units="ns")
    dut.i_rst.value = 0
    await Timer(50, units="ns")

    # ----- TEST 1: Continuous Mode Duty Cycle Verification -----
    dut._log.info("=== TEST 1: Continuous Mode Validation ===")
    test_duty = 0x000F
    dut.i_duty.value = test_duty
    dut.i_mode.value = 0  # `CONTINOUS_MODE
    
    # Wait for a few PWM periods
    await RisingEdge(dut.o_pwm)
    await FallingEdge(dut.o_pwm)
    
    # Measure High-Time (Duty)
    high_time_count = 0
    await RisingEdge(dut.i_clk)
    while dut.o_pwm.value == 1:
        high_time_count += 1
        await RisingEdge(dut.i_clk)
    
    assert high_time_count == test_duty, \
        f"✗ FAIL: Duty mismatch. Exp: {test_duty}, Got: {high_time_count}"
    dut._log.info(f"✓ PASS: Continuous Duty verified at {high_time_count} cycles")

    # ----- TEST 2: N-Cycle Mode Pulse Counting -----
    dut._log.info("=== TEST 2: N-Cycle Mode Validation ===")
    test_n = 5
    dut.i_n.value = test_n
    dut.i_mode.value = 1  # `N_CYCLES_MODE
    dut.i_duty.value = 0x0004
    
    # Trigger N-Cycles
    await RisingEdge(dut.i_clk)
    dut.i_trig.value = 1
    await Timer(100, units="ns")
    dut.i_trig.value = 0
    
    # Count rising edges of o_pwm
    pulse_count = 0
    # Wait a reasonable time for N cycles to complete
    timeout_ns = (int(dut.i_limit.value) * test_n * 10) + 1000
    
    # Monitor pulses
    try:
        for _ in range(test_n):
            await cocotb.triggers.with_timeout(RisingEdge(dut.o_pwm), timeout_ns, "ns")
            pulse_count += 1
            dut._log.info(f"Detected pulse {pulse_count}/{test_n}")
    except cocotb.result.SimTimeoutError:
        pass

    assert pulse_count == test_n, f"✗ FAIL: Expected {test_n} pulses, got {pulse_count}"
    
    # Verify it stays LOW after finishing
    await Timer(200, units="ns")
    assert dut.o_pwm.value == 0, "✗ FAIL: PWM output did not stay LOW after N-cycles finished"
    dut._log.info(f"✓ PASS: N-Cycle mode correctly generated {pulse_count} pulses")

    # ----- TEST 3: 100% Duty Cycle Corner Case -----
    dut._log.info("=== TEST 3: 100% Duty Cycle Corner Case ===")
    dut.i_mode.value = 0
    dut.i_duty.value = 0xFFFF # Greater than i_limit
    await Timer(500, units="ns")
    assert dut.o_pwm.value == 1, "✗ FAIL: PWM should be constant HIGH for 100% duty"
    
    dut._log.info("=== ALL ADVANCED PWM TESTS COMPLETE ===")

# ==============================================================================
# ✅ REQUIRED: Pytest wrapper
# ==============================================================================
def test_pwm_advanced_runner():
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent
    
    sources = [
        proj_path / "sources" / "pwm_gen.sv",
        proj_path / "sources" / "output_controller.sv",
        proj_path / "sources" / "generator.sv",
    ]
    
    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel="pwm_module",
        always=True,
    )
    
    runner.test(
        hdl_toplevel="pwm_module", 
        test_module="test_pwm_hidden", 
        waves=True 
    )
