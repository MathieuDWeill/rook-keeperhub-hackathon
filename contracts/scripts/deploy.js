const fs = require("fs");
const path = require("path");
const { ethers, network } = require("hardhat");

function required(name) {
  const value = process.env[name];
  if (!value) throw new Error(`Missing ${name} in root .env`);
  return value;
}

async function deriveKeeperHubExecutor() {
  const configured = process.env.KEEPERHUB_EXECUTOR_ADDRESS;
  if (configured) return configured;

  const apiKey = required("KEEPERHUB_API_KEY");
  if (!apiKey.startsWith("kh_")) {
    throw new Error("KEEPERHUB_API_KEY must be an organization key starting with kh_");
  }

  const baseUrl = (process.env.KEEPERHUB_BASE_URL || "https://app.keeperhub.com").replace(/\/$/, "");
  const chainId = Number(process.env.CHAIN_ID || "11155111");
  const response = await fetch(`${baseUrl}/api/execute/contract-call`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      contractAddress: "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
      chainId,
      functionName: "transfer",
      functionArgs: JSON.stringify(["0x000000000000000000000000000000000000dEaD", "1"]),
      abi: JSON.stringify([
        {
          inputs: [
            { name: "to", type: "address" },
            { name: "amount", type: "uint256" },
          ],
          name: "transfer",
          outputs: [{ name: "", type: "bool" }],
          stateMutability: "nonpayable",
          type: "function",
        },
      ]),
      simulate: true,
    }),
  });
  const body = await response.json().catch(() => ({}));
  const derived = body.from;
  if (!derived || !ethers.isAddress(derived)) {
    throw new Error(`Could not derive KeeperHub organization wallet from Direct Execution simulation: ${JSON.stringify(body)}`);
  }
  return derived;
}

async function main() {
  const [deployer] = await ethers.getSigners();
  const artisan = required("ARTISAN_ADDRESS");
  const keeperHubExecutor = await deriveKeeperHubExecutor();
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
  console.log("live-preflight and run-demo will read deployed addresses from artifacts/deployment.json");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
