import cocotb
import os
from pathlib import Path

from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, with_timeout, SimTimeoutError
from cocotb_tools.runner import get_runner


# ==============================================================================
# Cocotb Test: Advanced PWM Validation
# ==============================================================================
@cocotb.test()
async def test_pwm_advanced_complete(dut):
    """
    Validates Continuous and N-Cycle modes with period and duty cycle checking.
    """

    cocotb.log.info("Starting PWM Advanced Test")

    # Start 100MHz Clock (10ns period)
    cocotb.start_soon(Clock(dut.i_clk, 10, units="ns").start())

    # --------------------------
    # Reset Phase
    # --------------------------
    dut.i_rst.value = 1
    dut.i_trig.value = 0
    dut.i_mode.value = 0
    dut.i_duty.value = 0
    dut.i_limit.value = 0x7FFF
    dut.i_n.value = 0

    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)

    dut.i_rst.value = 0

    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)

    # ------------------------------------------------
    # TEST 1 : Continuous Mode Duty Cycle Verification
    # ------------------------------------------------
    cocotb.log.info("=== TEST 1: Continuous Mode Validation ===")

    test_duty = 0x000F
    dut.i_duty.value = test_duty
    dut.i_mode.value = 0  # CONTINUOUS MODE

    # Wait for PWM activity
    await RisingEdge(dut.o_pwm)
    await FallingEdge(dut.o_pwm)

    # Measure high time
    high_time_count = 0
    max_cycles = 10000

    await RisingEdge(dut.i_clk)

    while dut.o_pwm.value == 1 and high_time_count < max_cycles:
        high_time_count += 1
        await RisingEdge(dut.i_clk)

    assert high_time_count < max_cycles, "PWM stuck HIGH"

    assert high_time_count == test_duty, \
        f"FAIL: Duty mismatch. Expected {test_duty}, Got {high_time_count}"

    cocotb.log.info(f"PASS: Continuous Duty verified at {high_time_count} cycles")

    # ----------------------------------------
    # TEST 2 : N-Cycle Mode Pulse Counting
    # ----------------------------------------
    cocotb.log.info("=== TEST 2: N-Cycle Mode Validation ===")

    test_n = 5

    dut.i_n.value = test_n
    dut.i_mode.value = 1  # N_CYCLES_MODE
    dut.i_duty.value = 0x0004

    # Trigger
    await RisingEdge(dut.i_clk)
    dut.i_trig.value = 1
    await RisingEdge(dut.i_clk)
    dut.i_trig.value = 0

    pulse_count = 0

    timeout_ns = (dut.i_limit.value.integer * test_n * 10) + 1000

    try:
        for i in range(test_n):
            await with_timeout(RisingEdge(dut.o_pwm), timeout_ns, "ns")
            pulse_count += 1
            cocotb.log.info(f"Detected pulse {pulse_count}/{test_n}")

    except SimTimeoutError:
        cocotb.log.warning("Timeout waiting for PWM pulses")

    assert pulse_count == test_n, \
        f"FAIL: Expected {test_n} pulses, got {pulse_count}"

    # Verify PWM stops
    await Timer(200, units="ns")

    assert dut.o_pwm.value == 0, \
        "FAIL: PWM output did not stay LOW after N cycles finished"

    cocotb.log.info(f"PASS: N-Cycle mode generated {pulse_count} pulses")

    # ------------------------------------------------
    # TEST 3 : 100% Duty Cycle Corner Case
    # ------------------------------------------------
    cocotb.log.info("=== TEST 3: 100% Duty Cycle Corner Case ===")

    dut.i_mode.value = 0
    dut.i_duty.value = 0xFFFF

    await Timer(500, units="ns")

    assert dut.o_pwm.value == 1, \
        "FAIL: PWM should stay HIGH for 100% duty"

    cocotb.log.info("PASS: 100% duty cycle handled correctly")

    cocotb.log.info("=== ALL ADVANCED PWM TESTS COMPLETE ===")


# ==============================================================================
# Pytest Runner
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
        waves=True,
    )
