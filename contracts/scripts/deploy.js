const fs = require("fs");
const path = require("path");
const { ethers, network } = require("hardhat");

function required(name) {
  const value = process.env[name];
  if (!value) throw new Error(`Missing ${name} in root .env`);
  return value;
}

async function main() {
  const [deployer] = await ethers.getSigners();
  const artisan = required("ARTISAN_ADDRESS");
  const keeperHubExecutor = required("KEEPERHUB_EXECUTOR_ADDRESS");
  const fundedAmount = BigInt(process.env.FUNDED_AMOUNT_MINOR || "10000000000");
  const expiryDays = Number(process.env.ESCROW_EXPIRY_DAYS || "30");
  const latest = await ethers.provider.getBlock("latest");
  const expiresAt = BigInt(latest.timestamp + expiryDays * 24 * 60 * 60);

  console.log("Network:", network.name);
  console.log("Client/deployer:", deployer.address);
  console.log("Artisan:", artisan);
  console.log("KeeperHub executor:", keeperHubExecutor);

  const Token = await ethers.getContractFactory("MockUSDC");
  const token = await Token.deploy();
  await token.waitForDeployment();

  const Escrow = await ethers.getContractFactory("RookEscrow");
  const escrow = await Escrow.deploy(
    await token.getAddress(),
    deployer.address,
    artisan,
    fundedAmount,
    keeperHubExecutor,
    expiresAt
  );
  await escrow.waitForDeployment();

  await (await token.mint(deployer.address, fundedAmount)).wait();
  await (await token.approve(await escrow.getAddress(), fundedAmount)).wait();
  await (await escrow.fund()).wait();

  const deployment = {
    chainId: Number((await ethers.provider.getNetwork()).chainId),
    network: network.name,
    client: deployer.address,
    artisan,
    keeperHubExecutor,
    mockUsdc: await token.getAddress(),
    escrow: await escrow.getAddress(),
    fundedAmountMinor: fundedAmount.toString(),
    expiresAt: expiresAt.toString(),
    deployedAt: new Date().toISOString(),
  };

  const out = path.resolve(__dirname, "../../artifacts/deployment.json");
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, JSON.stringify(deployment, null, 2) + "\n");
  console.log(JSON.stringify(deployment, null, 2));
  console.log(`\nSaved ${out}`);
  console.log(`Set ESCROW_CONTRACT_ADDRESS=${deployment.escrow} in .env`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
