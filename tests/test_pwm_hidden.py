import cocotb
import os
from pathlib import Path

from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, with_timeout, SimTimeoutError
from cocotb_tools.runner import get_runner

N_CYCLES_MODE = 1
CONTINOUS_MODE = 0
# ==============================================================================
# Cocotb Test: Advanced PWM Validation
# ==============================================================================

@cocotb.test()
async def test_pwm_hidden(dut):

    # Initial values
    dut.i_duty.value = 0x0004
    dut.i_limit.value = 0x7FFF
    dut.i_mode.value = CONTINOUS_MODE
    dut.i_n.value = 0b101

    dut.i_trig.value = 0
    dut.i_rst.value = 0

    # Clock generation (10ns period)
    clock = Clock(dut.i_clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # ---------------- RESET ----------------
    await Timer(1, units="ns")
    dut.i_rst.value = 1

    await Timer(30, units="ns")
    dut.i_rst.value = 0

    await Timer(300, units="ns")

    # =====================================================
    # CONTINUOUS MODE
    # =====================================================

    dut.i_mode.value = CONTINOUS_MODE

    await Timer(1, units="us")

    dut.i_duty.value = 0x000F

    await Timer(100, units="ns")

    dut.i_trig.value = 1

    await Timer(100, units="ns")

    dut.i_trig.value = 0

    await Timer(2, units="ms")

    # =====================================================
    # N CYCLES MODE
    # =====================================================

    dut.i_mode.value = N_CYCLES_MODE

    await Timer(1, units="us")

    for i in range(1, 5):

        dut.i_duty.value = int(i * (dut.i_limit.value.integer // 4))

        dut.i_trig.value = 1

        await Timer(100, units="ns")

        dut.i_trig.value = 0

        await Timer(2, units="ms")

    await Timer(2, units="us")
async def pwm_test(dut):

    cocotb.start_soon(thread1(dut))
    cocotb.start_soon(thread2(dut))
    cocotb.start_soon(thread3(dut))
    cocotb.start_soon(thread4(dut))
    cocotb.start_soon(thread5(dut))

async def thread1(dut):

    while True:
        await RisingEdge(dut.i_clk)

        if dut.o_pwm.value:
            dut.duty_counter.value = dut.duty_counter.value.integer + 1
        else:
            await FallingEdge(dut.i_clk)
            dut.duty_counter.value = 0
            
async def thread2(dut):

    while True:
        await FallingEdge(dut.o_pwm)

        if dut.duty_counter.value.integer != dut.i_duty.value.integer:
            dut._log.warning(
                f"Duty Cycle mismatch. i_duty={dut.i_duty.value} duty_counter={dut.duty_counter.value}"
            )
            
            
async def thread3(dut):

    while True:

        await RisingEdge(dut.o_pwm)

        while dut.period_lenght.value.integer <= dut.i_limit.value.integer:

            await RisingEdge(dut.i_clk)

            dut.period_lenght.value = dut.period_lenght.value.integer + 1

            if dut.period_lenght.value.integer == dut.i_limit.value.integer - 1:

                dut.period_lenght.value = 0

                if (dut.i_duty.value.integer < (dut.i_limit.value.integer - 4)) and (dut.i_duty.value.integer != 0):

                    dut._log.info(
                        f"End of period PWM={dut.o_pwm.value}"
                    )

                    if dut.o_pwm.value:
                        dut._log.warning("PWM should be deasserted at end of period")
                        
                        
                        
async def thread4(dut):

    while True:

        await RisingEdge(dut.o_pwm)

        if dut.i_mode.value == 1:   # N_CYCLES_MODE
            dut.pulse_counter.value = dut.pulse_counter.value.integer + 1
async def thread5(dut):

    while True:

        await RisingEdge(dut.i_trig)

        if (dut.i_duty.value != 0 and
            dut.i_mode.value == 1 and
            dut.pulse_counter.value != 0):

            dut._log.info(
                f"End of mode pulse_counter={dut.pulse_counter.value} i_n={dut.i_n.value}"
            )

            if dut.pulse_counter.value.integer != dut.i_n.value.integer:
                dut._log.warning(
                    f"Pulse counter mismatch: {dut.pulse_counter.value} != {dut.i_n.value}"
                )

        await FallingEdge(dut.i_trig)

        if dut.pulse_counter.value.integer != 0:
            dut.pulse_counter.value = 0
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
