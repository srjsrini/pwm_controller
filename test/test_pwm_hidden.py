import cocotb
import os
from pathlib import Path
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from cocotb_tools.runner import get_runner
N_CYCLES_MODE = 1
CONTINOUS_MODE = 0


# ---------------- THREAD 1 ----------------
async def duty_counter_thread(dut):

    duty_counter = 0

    while True:

        await RisingEdge(dut.i_clk)

        if dut.o_pwm.value:
            duty_counter += 1
        else:
            await FallingEdge(dut.i_clk)
            duty_counter = 0

        dut._log.debug(f"Duty counter = {duty_counter}")


# ---------------- THREAD 2 ----------------
async def duty_check_thread(dut):

    duty_counter = 0

    while True:

        await FallingEdge(dut.o_pwm)

        if duty_counter != dut.i_duty.value.integer:

            dut._log.warning(
                f"Duty mismatch: expected {dut.i_duty.value.integer}, got {duty_counter}"
            )


# ---------------- THREAD 3 ----------------
async def period_measure_thread(dut):

    period_length = 0

    while True:

        await RisingEdge(dut.o_pwm)

        while period_length <= dut.i_limit.value.integer:

            await RisingEdge(dut.i_clk)

            period_length += 1

            if period_length == dut.i_limit.value.integer - 1:

                period_length = 0

                if (dut.i_duty.value.integer < (dut.i_limit.value.integer - 4)
                        and dut.i_duty.value.integer != 0):

                    dut._log.info(
                        f"End of period PWM={dut.o_pwm.value}"
                    )

                    if dut.o_pwm.value:
                        dut._log.warning("PWM should be low at end of period")


# ---------------- THREAD 4 ----------------
async def pulse_counter_thread(dut):

    pulse_counter = 0

    while True:

        await RisingEdge(dut.o_pwm)

        if dut.i_mode.value == N_CYCLES_MODE:

            pulse_counter += 1

            dut._log.info(f"Pulse count = {pulse_counter}")


# ---------------- THREAD 5 ----------------
async def pulse_check_thread(dut):

    pulse_counter = 0

    while True:

        await RisingEdge(dut.i_trig)

        if (dut.i_duty.value.integer != 0
                and dut.i_mode.value == N_CYCLES_MODE
                and pulse_counter != 0):

            dut._log.info(
                f"End of mode pulses={pulse_counter} expected={dut.i_n.value.integer}"
            )

            if pulse_counter != dut.i_n.value.integer:

                dut._log.warning(
                    f"Pulse mismatch {pulse_counter} != {dut.i_n.value.integer}"
                )

        await FallingEdge(dut.i_trig)

        if pulse_counter != 0:
            pulse_counter = 0


# ---------------- MAIN TEST ----------------
@cocotb.test()
async def pwm_test(dut):

    # Clock generation
    clock = Clock(dut.i_clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # fork...join_none equivalent
    cocotb.start_soon(duty_counter_thread(dut))
    cocotb.start_soon(duty_check_thread(dut))
    cocotb.start_soon(period_measure_thread(dut))
    cocotb.start_soon(pulse_counter_thread(dut))
    cocotb.start_soon(pulse_check_thread(dut))

    # ---------------- RESET ----------------
    await Timer(1, units="ns")
    dut.i_rst.value = 1

    await Timer(30, units="ns")
    dut.i_rst.value = 0

    await Timer(300, units="ns")

    # ---------------- CONTINUOUS MODE ----------------

    dut.i_mode.value = CONTINOUS_MODE

    await Timer(1, units="us")

    dut.i_duty.value = 0x000F

    await Timer(100, units="ns")

    dut.i_trig.value = 1
    await Timer(100, units="ns")
    dut.i_trig.value = 0

    await Timer(2, units="ms")

    # ---------------- N CYCLES MODE ----------------

    dut.i_mode.value = N_CYCLES_MODE

    await Timer(1, units="us")

    for i in range(1, 5):

        #dut.i_duty.value = int(i * (dut.i_limit.value.integer // 4))
    #    dut.i_duty.value = i * (dut.i_limit.value.integer // 4)
# Line 168: avoid .integer when signal has X/Z
        try:
            limit = int(dut.i_limit.value.to_unsigned())
        except ValueError:
            limit = 0  # or a default from your spec
        dut.i_duty.value = int(i * (limit // 4))
        dut.i_trig.value = 1
        await Timer(100, units="ns")
        dut.i_trig.value = 0

        await Timer(2, units="ms")

    await Timer(2, units="us")
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

