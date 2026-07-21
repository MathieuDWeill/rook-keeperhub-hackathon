// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/// @title RookEscrow
/// @notice Evidence-gated milestone escrow. Policy is evaluated offchain; only the
///         designated KeeperHub executor may settle approved mandates onchain.
contract RookEscrow is AccessControl, ReentrancyGuard {
    using SafeERC20 for IERC20;

    bytes32 public constant EXECUTOR_ROLE = keccak256("EXECUTOR_ROLE");

    IERC20 public immutable token;
    address public immutable client;
    address public immutable artisan;
    uint256 public immutable fundedAmount;
    uint64 public immutable expiresAt;

    uint256 public releasedAmount;
    bool public funded;
    mapping(bytes32 => bool) public consumedDecision;

    error ZeroAddress();
    error ZeroAmount();
    error ClientOnly();
    error AlreadyFunded();
    error NotFunded();
    error WrongRecipient();
    error DecisionReplay();
    error InvalidReleaseAmount();
    error NotExpired();
    error NothingToRefund();

    event EscrowFunded(uint256 amount);
    event MilestoneReleased(
        bytes32 indexed decisionId,
        bytes32 indexed milestoneId,
        address indexed recipient,
        uint256 amount
    );
    event ExpiredBalanceRefunded(uint256 amount);

    constructor(
        IERC20 token_,
        address client_,
        address artisan_,
        uint256 fundedAmount_,
        address executor_,
        uint64 expiresAt_
    ) {
        if (address(token_) == address(0) || client_ == address(0) || artisan_ == address(0) || executor_ == address(0)) {
            revert ZeroAddress();
        }
        if (fundedAmount_ == 0) revert ZeroAmount();
        if (expiresAt_ <= block.timestamp) revert NotExpired();

        token = token_;
        client = client_;
        artisan = artisan_;
        fundedAmount = fundedAmount_;
        expiresAt = expiresAt_;
        _grantRole(DEFAULT_ADMIN_ROLE, client_);
        _grantRole(EXECUTOR_ROLE, executor_);
    }

    function fund() external nonReentrant {
        if (msg.sender != client) revert ClientOnly();
        if (funded) revert AlreadyFunded();
        funded = true;
        token.safeTransferFrom(client, address(this), fundedAmount);
        emit EscrowFunded(fundedAmount);
    }

    function release(bytes32 decisionId, bytes32 milestoneId, address recipient, uint256 amount)
        external
        onlyRole(EXECUTOR_ROLE)
        nonReentrant
    {
        if (!funded) revert NotFunded();
        if (recipient != artisan) revert WrongRecipient();
        if (consumedDecision[decisionId]) revert DecisionReplay();
        if (amount == 0 || releasedAmount + amount > fundedAmount) revert InvalidReleaseAmount();

        consumedDecision[decisionId] = true;
        releasedAmount += amount;
        token.safeTransfer(recipient, amount);
        emit MilestoneReleased(decisionId, milestoneId, recipient, amount);
    }

    /// @notice The client can only recover the remaining balance after the escrow expiry.
    function refundExpiredBalance() external nonReentrant {
        if (msg.sender != client) revert ClientOnly();
        if (block.timestamp < expiresAt) revert NotExpired();
        uint256 amount = token.balanceOf(address(this));
        if (amount == 0) revert NothingToRefund();
        token.safeTransfer(client, amount);
        emit ExpiredBalanceRefunded(amount);
    }

    function remainingBalance() external view returns (uint256) {
        return token.balanceOf(address(this));
    }
}
