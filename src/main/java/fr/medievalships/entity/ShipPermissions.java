package fr.medievalships.entity;

import net.minecraft.command.permission.LeveledPermissionPredicate;
import net.minecraft.command.permission.PermissionPredicate;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.server.command.ServerCommandSource;

import fr.medievalships.data.ConfigManager;

/** Operator level checks (1.21.11 permission predicates). */
public final class ShipPermissions {
	private ShipPermissions() {
	}

	public static int level(PermissionPredicate permissions) {
		if (permissions == PermissionPredicate.ALL) {
			return 4;
		}
		if (permissions instanceof LeveledPermissionPredicate leveled) {
			return leveled.getLevel().getLevel();
		}
		return 0;
	}

	public static boolean isAdmin(ServerCommandSource source) {
		return level(source.getPermissions()) >= ConfigManager.server().adminPermissionLevel;
	}

	public static boolean isAdmin(PlayerEntity player) {
		return level(player.getPermissions()) >= ConfigManager.server().adminPermissionLevel;
	}
}
