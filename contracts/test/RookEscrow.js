const { expect } = require("chai");
const { ethers } = require("hardhat");

async function fixture() {
  const [client, artisan, executor, stranger] = await ethers.getSigners();
  const Token = await ethers.getContractFactory("MockUSDC");
  const token = await Token.deploy();
  const total = 10_000_000n;
  await token.mint(client.address, total);
  const latest = await ethers.provider.getBlock("latest");
  const expiry = BigInt(latest.timestamp + 7 * 24 * 60 * 60);
  const Escrow = await ethers.getContractFactory("RookEscrow");
  const escrow = await Escrow.deploy(
    token.target,
    client.address,
    artisan.address,
    total,
    executor.address,
    expiry
  );
  await token.connect(client).approve(escrow.target, total);
  await escrow.connect(client).fund();
  return { client, artisan, executor, stranger, token, escrow, total, expiry };
}

describe("RookEscrow", function () {
  it("funds and releases once through the KeeperHub executor", async function () {
    const { artisan, executor, token, escrow } = await fixture();
    const decision = ethers.id("decision-1");
    await expect(
      escrow.connect(executor).release(decision, ethers.id("milestone-1"), artisan.address, 3_000_000n)
    ).to.emit(escrow, "MilestoneReleased");
    expect(await token.balanceOf(artisan.address)).to.equal(3_000_000n);
    await expect(
      escrow.connect(executor).release(decision, ethers.id("milestone-1"), artisan.address, 1n)
    ).to.be.revertedWithCustomError(escrow, "DecisionReplay");
  });

  it("rejects non-executors and recipient substitution", async function () {
    const { artisan, executor, stranger, escrow } = await fixture();
    await expect(
      escrow.connect(stranger).release(ethers.id("d1"), ethers.id("m1"), artisan.address, 1n)
    ).to.be.reverted;
    await expect(
      escrow.connect(executor).release(ethers.id("d2"), ethers.id("m1"), stranger.address, 1n)
    ).to.be.revertedWithCustomError(escrow, "WrongRecipient");
  });

  it("prevents early client withdrawal but refunds after expiry", async function () {
    const { client, token, escrow, total, expiry } = await fixture();
    await expect(escrow.connect(client).refundExpiredBalance()).to.be.revertedWithCustomError(escrow, "NotExpired");
    await ethers.provider.send("evm_setNextBlockTimestamp", [Number(expiry)]);
    await ethers.provider.send("evm_mine");
    await escrow.connect(client).refundExpiredBalance();
    expect(await token.balanceOf(client.address)).to.equal(total);
  });
});
