package fr.medievalships.door;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import io.netty.buffer.ByteBuf;

import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;

/**
 * What a bound key carries (1.32.0, the data component {@code medievalships:serrure} of {@code medievalships:cle}): the
 * lock of its door ({@code serrure}, see {@link fr.medievalships.core.DoorKeys}) and the label of that door
 * ({@code porte}: its name, or its coordinates), shown in its tooltip ("Ouvre : ..."). A component of its own: renaming
 * the key at an anvil keeps it. Saved with the item and sent to the clients (for the tooltip).
 */
public record KeyLock(String lock, String label) {
	public static final Codec<KeyLock> CODEC = RecordCodecBuilder.create(i -> i.group(
			Codec.STRING.fieldOf("serrure").forGetter(KeyLock::lock),
			Codec.STRING.optionalFieldOf("porte", "").forGetter(KeyLock::label)).apply(i, KeyLock::new));
	public static final PacketCodec<ByteBuf, KeyLock> PACKET_CODEC = PacketCodec.tuple(PacketCodecs.STRING, KeyLock::lock, PacketCodecs.STRING,
			KeyLock::label, KeyLock::new);

	public KeyLock {
		lock = lock == null ? "" : lock;
		label = label == null ? "" : label;
	}
}
